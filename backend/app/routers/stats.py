from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services.position import compute_position

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    sessions = db.query(models.InfiniteSession).order_by(models.InfiniteSession.id.asc()).all()
    closed = [s for s in sessions if s.status in ("completed", "quartered")]
    active = next((s for s in sessions if s.status == "active"), None)

    def avg(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    profits = [s.final_profit_pct for s in closed]
    cycles = [
        {
            "id": s.id,
            "status": s.status,
            "final_profit_pct": s.final_profit_pct,
            "final_profit_krw": s.final_profit_krw,
            "total_turns": s.total_turns,
        }
        for s in closed
    ]

    current = None
    if active:
        pos = compute_position(db, active)
        last = (
            db.query(models.DailyState)
            .filter(models.DailyState.session_id == active.id)
            .order_by(models.DailyState.date.desc())
            .first()
        )
        current = {
            "id": active.id,
            "turn_number": pos["turn_number"],
            "mode": pos["mode"],
            "holding_qty": pos["holding_qty"],
            "avg_price_usd": pos["avg_price_usd"],
            "profit_pct": last.profit_pct if last else None,
            "eval_value_krw": last.eval_value_krw if last else None,
        }

    return {
        "total_cycles": len(sessions),
        "active_cycles": 1 if active else 0,
        "closed_cycles": len(closed),
        "avg_turns": avg([s.total_turns for s in closed]),
        "avg_profit_pct": avg(profits),
        "cum_profit_krw": sum(s.final_profit_krw or 0 for s in closed),
        "best_profit_pct": max(profits) if profits else None,
        "worst_profit_pct": min(profits) if profits else None,
        "current": current,
        "cycles": cycles,
    }
