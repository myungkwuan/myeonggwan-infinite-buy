from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.app_config import get_or_create_config
from app.services.position import compute_position
from app.services import market

router = APIRouter(prefix="/session", tags=["session"])


def resolve_rate(db, override):
    """환율 결정: 수동 > 자동조회 > config 직전값."""
    cfg = get_or_create_config(db)
    if override:
        return float(override)
    if cfg.auto_rate:
        r = market.get_usd_krw_rate()
        if r:
            return float(r)
    return float(cfg.usd_krw_rate)


def get_active(db):
    return (
        db.query(models.InfiniteSession)
        .filter(models.InfiniteSession.status == "active")
        .first()
    )


@router.post("", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    if get_active(db):
        raise HTTPException(
            status_code=400,
            detail="이미 활성 사이클이 있습니다. 종료 후 새로 시작하세요.",
        )
    cfg = get_or_create_config(db)
    seed_krw = payload.seed_krw or cfg.seed_krw
    divisions = payload.divisions or cfg.divisions
    target_pct = payload.target_pct if payload.target_pct is not None else cfg.target_pct
    rate = resolve_rate(db, payload.usd_krw_rate)

    seed_usd = seed_krw / rate
    per_turn_usd = seed_usd / divisions

    s = models.InfiniteSession(
        ticker=payload.ticker or cfg.ticker,
        seed_krw=seed_krw,
        seed_usd=round(seed_usd, 2),
        divisions=divisions,
        per_turn_usd=round(per_turn_usd, 2),
        target_pct=target_pct,
        usd_krw_rate=rate,
        status="active",
        memo=payload.memo,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/current")
def get_current(db: Session = Depends(get_db)):
    s = get_active(db)
    if not s:
        # 활성 사이클 없음 — 404 대신 200+null (프론트 콘솔 에러 방지)
        return {"session": None, "position": None}
    return {
        "session": schemas.SessionOut.model_validate(s).model_dump(mode="json"),
        "position": compute_position(db, s),
    }


@router.get("/history")
def history(db: Session = Depends(get_db)):
    """전체 사이클 목록 (최신순) + 현재 포지션 요약."""
    sessions = (
        db.query(models.InfiniteSession)
        .order_by(models.InfiniteSession.id.desc())
        .all()
    )
    out = []
    for s in sessions:
        pos = compute_position(db, s)
        out.append({
            "id": s.id,
            "ticker": s.ticker,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "divisions": s.divisions,
            "per_turn_usd": s.per_turn_usd,
            "usd_krw_rate": s.usd_krw_rate,
            "target_pct": s.target_pct,
            "turn_number": pos["turn_number"],
            "mode": pos["mode"],
            "holding_qty": pos["holding_qty"],
            "avg_price_usd": pos["avg_price_usd"],
            "final_profit_pct": s.final_profit_pct,
            "final_profit_krw": s.final_profit_krw,
        })
    return {"sessions": out}


@router.post("/{session_id}/close")
def close_session(session_id: int, status: str = "completed", db: Session = Depends(get_db)):
    """사이클 수동 종료 — 그때까지의 체결 기준으로 최종 수익 기록.

    status: completed(익절 완료) / quartered(쿼터 종료)
    final_profit = (매도대금 + 잔여보유 평가) - 총매수원가
    """
    if status not in ("completed", "quartered"):
        raise HTTPException(status_code=400, detail="status는 completed/quartered만 가능합니다.")
    s = (
        db.query(models.InfiniteSession)
        .filter(models.InfiniteSession.id == session_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="해당 사이클을 찾을 수 없습니다.")
    if s.status != "active":
        raise HTTPException(status_code=400, detail="이미 종료된 사이클입니다.")

    pos = compute_position(db, s)
    holding = pos["holding_qty"]
    buy_cost = pos["total_buy_cost_usd"]

    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.session_id == s.id,
            models.Transaction.is_executed == True,  # noqa: E712
        )
        .all()
    )
    sell_proceeds = sum(t.quantity * t.price_usd for t in txns if t.action == "sell")

    last = (
        db.query(models.DailyState)
        .filter(models.DailyState.session_id == s.id)
        .order_by(models.DailyState.date.desc())
        .first()
    )
    price = (last.soxl_close if last and last.soxl_close else None)         or market.get_soxl_close() or pos["avg_price_usd"]
    rate = (last.usd_krw_rate if last and last.usd_krw_rate else None) or s.usd_krw_rate

    final_usd = sell_proceeds + holding * (price or 0) - buy_cost
    final_pct = (final_usd / buy_cost * 100.0) if buy_cost else 0.0
    final_krw = final_usd * rate

    s.status = status
    s.ended_at = datetime.utcnow()
    s.final_profit_pct = round(final_pct, 2)
    s.final_profit_krw = round(final_krw)
    s.total_turns = pos["turn_number"]
    db.commit()
    db.refresh(s)

    return {
        "id": s.id,
        "status": s.status,
        "final_profit_pct": s.final_profit_pct,
        "final_profit_krw": s.final_profit_krw,
        "final_profit_usd": round(final_usd, 2),
        "total_turns": s.total_turns,
    }


@router.post("/{session_id}/reopen")
def reopen_session(session_id: int, db: Session = Depends(get_db)):
    """종료한 사이클을 다시 진행 중으로 되돌림 (실수 복구).

    다른 활성 사이클이 있으면 차단 — 활성은 항상 하나만.
    """
    s = (
        db.query(models.InfiniteSession)
        .filter(models.InfiniteSession.id == session_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="해당 사이클을 찾을 수 없습니다.")
    if s.status == "active":
        raise HTTPException(status_code=400, detail="이미 진행 중인 사이클입니다.")
    if get_active(db):
        raise HTTPException(
            status_code=400,
            detail="다른 활성 사이클이 있어 되돌릴 수 없습니다. 먼저 그 사이클을 종료하세요.",
        )
    s.status = "active"
    s.ended_at = None
    s.final_profit_pct = None
    s.final_profit_krw = None
    s.total_turns = None
    db.commit()
    db.refresh(s)
    return {"id": s.id, "status": s.status}
