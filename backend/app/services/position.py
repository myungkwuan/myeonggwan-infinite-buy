"""현재 포지션(평단·보유수량·T값) 계산 — 체결 Transaction을 단일 진실원천으로."""

from app import models
from app.logic.infinite_v22 import calc_turn, calc_mode


def compute_position(db, session):
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.session_id == session.id,
            models.Transaction.is_executed == True,  # noqa: E712
        )
        .all()
    )
    buy_qty = sum(t.quantity for t in txns if t.action == "buy")
    buy_cost = sum(t.quantity * t.price_usd for t in txns if t.action == "buy")
    sell_qty = sum(t.quantity for t in txns if t.action == "sell")

    avg = buy_cost / buy_qty if buy_qty > 0 else 0.0
    holding = max(0, buy_qty - sell_qty)
    remaining_cost = holding * avg
    t_val = calc_turn(buy_cost, session.per_turn_usd)

    return {
        "turn_number": round(t_val, 4),
        "mode": calc_mode(t_val),
        "holding_qty": int(round(holding)),
        "avg_price_usd": round(avg, 4),
        "total_buy_cost_usd": round(buy_cost, 2),
        "remaining_cost_usd": round(remaining_cost, 2),
    }
