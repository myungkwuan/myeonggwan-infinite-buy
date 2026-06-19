from app.logic.infinite_v22 import (
    calc_turn, calc_mode, calc_buy_orders, calc_sell_orders,
    calc_evaluation, split_quantity,
)

RATE = 1390.0
PER_TURN = 9000.0


def test_calc_turn():
    assert calc_turn(0, PER_TURN) == 0
    assert calc_turn(18000, PER_TURN) == 2
    assert calc_turn(9000, 0) == 0  # per_turn 0 방어


def test_mode_boundaries():
    assert calc_mode(0) == "전반전"
    assert calc_mode(19) == "전반전"     # 경계: 전반전
    assert calc_mode(19.5) == "쿼터"
    assert calc_mode(20) == "후반전"     # 경계: 후반전
    assert calc_mode(24) == "후반전"


def test_split_quantity():
    assert split_quantity(900) == (225, 675)
    assert split_quantity(0) == (0, 0)
    assert split_quantity(10) == (3, 7)  # 2.5 → 반올림 3


def test_buy_jeonban():  # 전반전 T=0, 평단 20
    o = calc_buy_orders(20.0, 0.0, PER_TURN, RATE)
    assert len(o) == 2
    a, b = o
    assert a["order_type"] == "LOC" and a["price_usd"] == 20.0
    assert a["quantity"] == 225 and a["amount_usd"] == 4500.0
    assert a["amount_krw"] == round(4500.0 * RATE)
    # ② 평단+10% → 22.0, floor(4500/22)=204
    assert b["price_usd"] == 22.0 and b["quantity"] == 204


def test_buy_quarter_empty():
    assert calc_buy_orders(20.0, 19.5, PER_TURN, RATE) == []


def test_buy_hooban():  # 후반전 T=20: -15% → 17.0, floor(9000/17)=529
    o = calc_buy_orders(20.0, 20.0, PER_TURN, RATE)
    assert len(o) == 1
    assert o[0]["price_usd"] == 17.0 and o[0]["quantity"] == 529


def test_buy_first_day_base_price():  # 보유0 첫날: 현재가를 base로
    o = calc_buy_orders(25.0, 0.0, PER_TURN, RATE)
    assert o[0]["price_usd"] == 25.0


def test_buy_invalid_price():
    assert calc_buy_orders(0, 0, PER_TURN, RATE) == []
    assert calc_buy_orders(None, 0, PER_TURN, RATE) == []


def test_sell_jeonban():  # 전반전 T=0, 보유 900
    o = calc_sell_orders(20.0, 0.0, 900, RATE)
    assert len(o) == 2
    q, tp = o
    assert q["order_type"] == "LOC" and q["price_usd"] == 23.0 and q["quantity"] == 225
    assert tp["order_type"] == "지정가" and tp["price_usd"] == 24.0 and tp["quantity"] == 675


def test_sell_quarter_moc():  # 쿼터: 1/4 MOC + 3/4 지정가
    o = calc_sell_orders(20.0, 19.5, 900, RATE)
    assert len(o) == 2
    assert o[0]["order_type"] == "MOC" and o[0]["price_usd"] is None
    assert o[0]["amount_usd"] is None and o[0]["amount_krw"] is None
    assert o[1]["order_type"] == "지정가" and o[1]["price_usd"] == 24.0


def test_sell_hooban_clamp():  # 후반전 T=24: 15-36=-21 → 하한 -20% → 16.0
    o = calc_sell_orders(20.0, 24.0, 900, RATE)
    assert o[0]["price_usd"] == 16.0
    assert o[1]["price_usd"] == 24.0


def test_sell_no_holdings():
    assert calc_sell_orders(20.0, 0.0, 0, RATE) == []
    assert calc_sell_orders(20.0, 0.0, None, RATE) == []


def test_evaluation_usd_krw():
    e = calc_evaluation(900, 20.0, 18000.0, 24.0, RATE)
    assert e["eval_value_usd"] == 21600.0
    assert e["profit_usd"] == 3600.0
    assert e["profit_pct"] == 20.0
    assert e["eval_value_krw"] == round(21600.0 * RATE)
    assert e["profit_krw"] == round(3600.0 * RATE)
