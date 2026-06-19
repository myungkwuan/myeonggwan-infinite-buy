"""환율(USD/KRW)·종목 시세(SOXL) 자동조회 (무료·API키 불필요).

소스 다중화로 가용성 확보:
  FX   : open.er-api.com → frankfurter.dev → frankfurter.app
  시세 : Yahoo Finance(UA 헤더) → Stooq CSV

각 함수는 실패 시 None을 반환하고, *_debug 함수는 소스/값/에러를 함께 돌려준다.
파싱 함수(_parse_*)는 순수 함수라 단위 테스트로 검증한다.
"""

from __future__ import annotations

import csv
import io

import httpx

TIMEOUT = 10.0
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


# ---------------- 파싱 (순수 함수) ----------------
def _parse_fx(data) -> float | None:
    """frankfurter 형식: {"rates": {"KRW": ...}}"""
    try:
        rate = (data or {}).get("rates", {}).get("KRW")
        return float(rate) if rate else None
    except (TypeError, ValueError, AttributeError):
        return None


def _parse_fx_erapi(data) -> float | None:
    """open.er-api.com 형식: {"result":"success","rates":{"KRW":...}}"""
    try:
        if (data or {}).get("result") != "success":
            return None
        rate = data.get("rates", {}).get("KRW")
        return float(rate) if rate else None
    except (TypeError, ValueError, AttributeError):
        return None


def _parse_yahoo(data) -> float | None:
    """Yahoo chart 형식에서 regularMarketPrice 추출."""
    try:
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        return float(price) if price else None
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def _parse_stooq_csv(text) -> float | None:
    try:
        rows = list(csv.DictReader(io.StringIO(text or "")))
        if not rows:
            return None
        close = rows[0].get("Close")
        if close in (None, "", "N/D"):
            return None
        return float(close)
    except (ValueError, KeyError):
        return None


# ---------------- HTTP ----------------
def _get(url: str):
    return httpx.get(url, timeout=TIMEOUT, headers={"User-Agent": UA}, follow_redirects=True)


_FX_SOURCES = [
    ("er-api", "https://open.er-api.com/v6/latest/USD", _parse_fx_erapi),
    ("frankfurter.dev", "https://api.frankfurter.dev/v1/latest?base=USD&symbols=KRW", _parse_fx),
    ("frankfurter.app", "https://api.frankfurter.app/latest?from=USD&to=KRW", _parse_fx),
]


# ---------------- 환율 ----------------
def get_usd_krw_rate_debug() -> dict:
    errors = []
    for name, url, parser in _FX_SOURCES:
        try:
            r = _get(url)
            r.raise_for_status()
            val = parser(r.json())
            if val:
                return {"ok": True, "source": name, "value": round(val, 2), "error": None}
            errors.append(f"{name}: KRW 없음")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {type(e).__name__}")
    return {"ok": False, "source": None, "value": None, "error": " | ".join(errors)}


def get_usd_krw_rate() -> float | None:
    return get_usd_krw_rate_debug()["value"]


# ---------------- 시세 ----------------
def get_stock_close_debug(ticker: str = "SOXL") -> dict:
    sym = ticker.split(".")[0].upper()
    errors = []
    # 1) Yahoo
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
        r = _get(url)
        r.raise_for_status()
        val = _parse_yahoo(r.json())
        if val:
            return {"ok": True, "source": "yahoo", "value": round(val, 4), "error": None}
        errors.append("yahoo: 가격 없음")
    except Exception as e:  # noqa: BLE001
        errors.append(f"yahoo: {type(e).__name__}")
    # 2) Stooq
    try:
        url = f"https://stooq.com/q/l/?s={sym.lower()}.us&f=sd2t2ohlcv&h&e=csv"
        r = _get(url)
        r.raise_for_status()
        val = _parse_stooq_csv(r.text)
        if val:
            return {"ok": True, "source": "stooq", "value": round(val, 4), "error": None}
        errors.append("stooq: N/D")
    except Exception as e:  # noqa: BLE001
        errors.append(f"stooq: {type(e).__name__}")
    return {"ok": False, "source": None, "value": None, "error": " | ".join(errors)}


def get_stock_close(symbol: str) -> float | None:
    return get_stock_close_debug(symbol)["value"]


def get_soxl_close() -> float | None:
    return get_stock_close_debug("SOXL")["value"]


def get_market_snapshot(ticker: str = "SOXL") -> dict:
    return {"usd_krw_rate": get_usd_krw_rate(), "price": get_stock_close(ticker)}


def check(ticker: str = "SOXL") -> dict:
    """진단용 — FX/시세 각 소스 시도 결과를 그대로 반환."""
    return {"fx": get_usd_krw_rate_debug(), "price": get_stock_close_debug(ticker)}
