from datetime import datetime, date as date_type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/backup", tags=["backup"])


def _dt(v):
    return v.isoformat() if v else None


def _ses(s):
    return {
        "id": s.id, "ticker": s.ticker, "seed_krw": s.seed_krw, "seed_usd": s.seed_usd,
        "divisions": s.divisions, "per_turn_usd": s.per_turn_usd, "target_pct": s.target_pct,
        "version": s.version, "usd_krw_rate": s.usd_krw_rate,
        "started_at": _dt(s.started_at), "ended_at": _dt(s.ended_at), "status": s.status,
        "final_profit_pct": s.final_profit_pct, "final_profit_krw": s.final_profit_krw,
        "total_turns": s.total_turns, "memo": s.memo,
    }


def _ds(d):
    return {
        "id": d.id, "session_id": d.session_id, "date": _dt(d.date),
        "turn_number": d.turn_number, "cumulative_quantity": d.cumulative_quantity,
        "cumulative_cost_usd": d.cumulative_cost_usd, "avg_price_usd": d.avg_price_usd,
        "soxl_close": d.soxl_close, "mode": d.mode,
        "buy_orders": d.buy_orders, "sell_orders": d.sell_orders,
        "eval_value_usd": d.eval_value_usd, "profit_pct": d.profit_pct, "profit_usd": d.profit_usd,
        "usd_krw_rate": d.usd_krw_rate, "eval_value_krw": d.eval_value_krw, "profit_krw": d.profit_krw,
    }


def _tx(t):
    return {
        "id": t.id, "session_id": t.session_id, "daily_state_id": t.daily_state_id,
        "date": _dt(t.date), "turn_number": t.turn_number, "action": t.action,
        "order_type": t.order_type, "quantity": t.quantity, "price_usd": t.price_usd,
        "total_usd": t.total_usd, "is_executed": t.is_executed, "memo": t.memo,
    }


@router.get("/export")
def export_all(db: Session = Depends(get_db)):
    """전체 데이터 JSON 스냅샷."""
    cfg = db.query(models.AppConfig).filter(models.AppConfig.id == 1).first()
    config = None
    if cfg:
        config = {
            "ticker": cfg.ticker, "seed_krw": cfg.seed_krw, "divisions": cfg.divisions,
            "target_pct": cfg.target_pct, "usd_krw_rate": cfg.usd_krw_rate,
            "auto_rate": cfg.auto_rate, "version": cfg.version,
        }
    return {
        "version": "v2.2",
        "exported_at": datetime.utcnow().isoformat(),
        "config": config,
        "sessions": [_ses(s) for s in db.query(models.InfiniteSession).order_by(models.InfiniteSession.id).all()],
        "daily_states": [_ds(d) for d in db.query(models.DailyState).order_by(models.DailyState.id).all()],
        "transactions": [_tx(t) for t in db.query(models.Transaction).order_by(models.Transaction.id).all()],
    }


def _pdate(v):
    return date_type.fromisoformat(v) if v else None


def _pdt(v):
    return datetime.fromisoformat(v) if v else None


@router.post("/import")
def import_all(payload: dict, db: Session = Depends(get_db)):
    """JSON 스냅샷으로 전체 복원 (기존 데이터 전부 교체). ID는 새로 매핑."""
    if not isinstance(payload, dict) or "sessions" not in payload:
        raise HTTPException(status_code=400, detail="올바른 백업 파일이 아닙니다.")
    try:
        # 기존 데이터 삭제 (FK 순서)
        db.query(models.Transaction).delete()
        db.query(models.DailyState).delete()
        db.query(models.InfiniteSession).delete()
        db.flush()

        ses_map, ds_map = {}, {}
        for s in payload.get("sessions", []):
            obj = models.InfiniteSession(
                ticker=s.get("ticker", "SOXL"), seed_krw=s["seed_krw"], seed_usd=s["seed_usd"],
                divisions=s.get("divisions", 40), per_turn_usd=s["per_turn_usd"],
                target_pct=s.get("target_pct", 20.0), version=s.get("version", "v2.2"),
                usd_krw_rate=s.get("usd_krw_rate", 1390.0),
                started_at=_pdt(s.get("started_at")) or datetime.utcnow(),
                ended_at=_pdt(s.get("ended_at")), status=s.get("status", "active"),
                final_profit_pct=s.get("final_profit_pct"), final_profit_krw=s.get("final_profit_krw"),
                total_turns=s.get("total_turns"), memo=s.get("memo"),
            )
            db.add(obj); db.flush()
            ses_map[s.get("id")] = obj.id

        for d in payload.get("daily_states", []):
            obj = models.DailyState(
                session_id=ses_map.get(d["session_id"]), date=_pdate(d.get("date")),
                turn_number=d.get("turn_number", 0), cumulative_quantity=d.get("cumulative_quantity", 0),
                cumulative_cost_usd=d.get("cumulative_cost_usd", 0), avg_price_usd=d.get("avg_price_usd", 0),
                soxl_close=d.get("soxl_close"), mode=d.get("mode", "전반전"),
                buy_orders=d.get("buy_orders"), sell_orders=d.get("sell_orders"),
                eval_value_usd=d.get("eval_value_usd"), profit_pct=d.get("profit_pct"),
                profit_usd=d.get("profit_usd"), usd_krw_rate=d.get("usd_krw_rate"),
                eval_value_krw=d.get("eval_value_krw"), profit_krw=d.get("profit_krw"),
            )
            db.add(obj); db.flush()
            ds_map[d.get("id")] = obj.id

        for t in payload.get("transactions", []):
            db.add(models.Transaction(
                session_id=ses_map.get(t["session_id"]),
                daily_state_id=ds_map.get(t.get("daily_state_id")),
                date=_pdate(t.get("date")), turn_number=t.get("turn_number"),
                action=t["action"], order_type=t.get("order_type"),
                quantity=t["quantity"], price_usd=t["price_usd"], total_usd=t.get("total_usd", 0),
                is_executed=t.get("is_executed", True), memo=t.get("memo"),
            ))

        cfg_data = payload.get("config")
        if cfg_data:
            cfg = db.query(models.AppConfig).filter(models.AppConfig.id == 1).first()
            if not cfg:
                cfg = models.AppConfig(id=1); db.add(cfg)
            for k in ("ticker", "seed_krw", "divisions", "target_pct", "usd_krw_rate", "auto_rate"):
                if k in cfg_data:
                    setattr(cfg, k, cfg_data[k])

        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=400, detail=f"복원 실패: {type(e).__name__}")

    return {
        "restored": {
            "sessions": len(payload.get("sessions", [])),
            "daily_states": len(payload.get("daily_states", [])),
            "transactions": len(payload.get("transactions", [])),
        }
    }
