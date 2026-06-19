from app.services.market import _parse_fx, _parse_stooq_csv


def test_parse_fx_ok():
    data = {"amount": 1.0, "base": "USD", "date": "2026-06-18", "rates": {"KRW": 1387.42}}
    assert _parse_fx(data) == 1387.42


def test_parse_fx_missing():
    assert _parse_fx({}) is None
    assert _parse_fx({"rates": {}}) is None
    assert _parse_fx(None) is None


def test_parse_stooq_ok():
    text = (
        "Symbol,Date,Time,Open,High,Low,Close,Volume\n"
        "SOXL.US,2026-06-17,22:00:00,24.10,24.90,23.80,24.55,1000000\n"
    )
    assert _parse_stooq_csv(text) == 24.55


def test_parse_stooq_nd():
    text = (
        "Symbol,Date,Time,Open,High,Low,Close,Volume\n"
        "SOXL.US,N/D,N/D,N/D,N/D,N/D,N/D,N/D\n"
    )
    assert _parse_stooq_csv(text) is None


def test_parse_stooq_empty():
    assert _parse_stooq_csv("") is None


def test_parse_fx_erapi_ok():
    from app.services.market import _parse_fx_erapi
    data = {"result": "success", "rates": {"KRW": 1391.5}}
    assert _parse_fx_erapi(data) == 1391.5


def test_parse_fx_erapi_fail():
    from app.services.market import _parse_fx_erapi
    assert _parse_fx_erapi({"result": "error"}) is None
    assert _parse_fx_erapi({}) is None


def test_parse_yahoo_ok():
    from app.services.market import _parse_yahoo
    data = {"chart": {"result": [{"meta": {"regularMarketPrice": 24.61}}]}}
    assert _parse_yahoo(data) == 24.61


def test_parse_yahoo_fail():
    from app.services.market import _parse_yahoo
    assert _parse_yahoo({}) is None
    assert _parse_yahoo({"chart": {"result": []}}) is None
