"""라오어 무한매수법 v2.2 핵심 계산 로직 (SOXL).

순수 함수 모듈 — DB/네트워크 의존성 없음. 입력값만으로 결정적 계산.
매수/매도 모두 '수량(정수)'까지 확정해 USD/KRW를 함께 반환한다.

모드 판정 우선순위(확정):
    쿼터(19 < T < 20) → 후반전(T >= 20) → 전반전(T <= 19)
"""

from __future__ import annotations

import math

QUARTER_LOW = 19.0
QUARTER_HIGH = 20.0


def _round_half_up(x: float) -> int:
    """반올림(round-half-up). 파이썬 기본 round의 banker's rounding 회피."""
    return math.floor(x + 0.5)


def _round_price(price: float) -> float:
    """미국주식 호가단위($0.01)에 맞춰 센트 반올림."""
    return round(price, 2)


def _qty_for_budget(budget_usd: float, price_usd: float) -> int:
    """예산 안에서 살 수 있는 최대 정수 수량 (내림)."""
    if price_usd <= 0:
        return 0
    return math.floor(budget_usd / price_usd)


def _make_order(label, order_type, qty, price_usd, rate, note=""):
    if price_usd is None:  # MOC 등 가격 미정
        amount_usd = None
        amount_krw = None
    else:
        amount_usd = round(qty * price_usd, 2)
        amount_krw = round(amount_usd * rate)
    return {
        "label": label,
        "order_type": order_type,          # LOC / MOC / 지정가
        "quantity": int(qty),
        "price_usd": price_usd,
        "amount_usd": amount_usd,
        "amount_krw": amount_krw,
        "note": note,
    }


def calc_turn(cumulative_cost_usd: float, per_turn_usd: float) -> float:
    """T값 = 누적 매수금액 / 회당 매수금액."""
    if per_turn_usd <= 0:
        return 0.0
    return cumulative_cost_usd / per_turn_usd


def calc_mode(t: float) -> str:
    """전반전 / 쿼터 / 후반전 판정 (쿼터 우선)."""
    if QUARTER_LOW < t < QUARTER_HIGH:
        return "쿼터"
    if t >= QUARTER_HIGH:
        return "후반전"
    return "전반전"


def split_quantity(total_qty: float) -> tuple[int, int]:
    """보유수량 → 1/4(반올림) / 3/4(나머지)."""
    total = _round_half_up(total_qty)
    quarter = _round_half_up(total / 4)
    quarter = max(0, min(quarter, total))
    return quarter, total - quarter


def calc_buy_orders(base_price, t, per_turn_usd, rate):
    """당일 매수 LOC 주문 목록.

    base_price: 평단가. 첫날(보유 0)에는 호출측이 현재 SOXL가를 넣는다.
    """
    orders = []
    if base_price is None or base_price <= 0:
        return orders

    mode = calc_mode(t)

    if mode == "쿼터":
        return orders  # 매수 안 함

    if mode == "후반전":
        discount = 1.5 * t - 15.0  # %
        price = _round_price(base_price * (1 - discount / 100.0))
        qty = _qty_for_budget(per_turn_usd, price)
        if qty > 0:
            orders.append(_make_order(
                "많이 빠지면 매수", "LOC", qty, price, rate,
                note=f"종가가 평단 -{discount:.2f}% 이하면 매수",
            ))
        return orders

    # 전반전 (T <= 19): 회당 50% + 50%
    half = per_turn_usd * 0.5
    price1 = _round_price(base_price)
    qty1 = _qty_for_budget(half, price1)
    if qty1 > 0:
        orders.append(_make_order(
            "평단가에 매수", "LOC", qty1, price1, rate,
            note="종가가 평단가 이하면 매수",
        ))
    premium = 10.0 - t / 2.0
    price2 = _round_price(base_price * (1 + premium / 100.0))
    qty2 = _qty_for_budget(half, price2)
    if qty2 > 0:
        orders.append(_make_order(
            "조금 비싸도 매수", "LOC", qty2, price2, rate,
            note=f"종가가 평단 +{premium:.2f}% 이하면 매수",
        ))
    return orders


def calc_sell_orders(avg_price, t, holding_qty, rate, target_pct=20.0):
    """당일 매도 주문 목록 (1/4 + 3/4)."""
    orders = []
    if not holding_qty or holding_qty <= 0 or not avg_price or avg_price <= 0:
        return orders

    mode = calc_mode(t)
    quarter, three_quarter = split_quantity(holding_qty)

    if mode == "쿼터":
        if quarter > 0:
            orders.append(_make_order(
                "일부 매도 (1/4)", "MOC", quarter, None, rate,
                note="종가에 무조건 매도",
            ))
    else:
        # 전반전/후반전 1/4: 평단 +(15 - 1.5T)% LOC. 후반전은 하한 -20%.
        prem = 15.0 - 1.5 * t
        if mode == "후반전":
            prem = max(prem, -20.0)
        q_price = _round_price(avg_price * (1 + prem / 100.0))
        if quarter > 0:
            sign = "+" if prem >= 0 else "-"
            orders.append(_make_order(
                "일부 매도 (1/4)", "LOC", quarter, q_price, rate,
                note=f"종가가 평단 {sign}{abs(prem):.2f}% 이상이면 매도",
            ))

    # 3/4 익절: 평단 +target_pct% 지정가 (항상 존재)
    if three_quarter > 0:
        tp_price = _round_price(avg_price * (1 + target_pct / 100.0))
        orders.append(_make_order(
            "익절 (+%.0f%%)" % target_pct, "지정가", three_quarter, tp_price, rate,
            note="목표가 도달 시 매도",
        ))
    return orders


def calc_evaluation(holding_qty, avg_price, cumulative_cost_usd, current_price, rate):
    """평가액·손익 (USD/KRW 동시)."""
    qty = holding_qty or 0
    cur = current_price or 0
    eval_usd = round(qty * cur, 2)
    profit_usd = round(eval_usd - (cumulative_cost_usd or 0), 2)
    if avg_price and avg_price > 0 and cur:
        profit_pct = round((cur / avg_price - 1) * 100, 2)
    else:
        profit_pct = 0.0
    return {
        "eval_value_usd": eval_usd,
        "profit_usd": profit_usd,
        "profit_pct": profit_pct,
        "eval_value_krw": round(eval_usd * rate),
        "profit_krw": round(profit_usd * rate),
    }
