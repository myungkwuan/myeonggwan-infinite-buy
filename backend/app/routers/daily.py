from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.app_config import get_or_create_config
from app.services.position import compute_position
from app.services import market
from app.logic.infinite_v22 import calc_buy_orders, calc_sell_orders, calc_evaluation

router = APIRouter(prefix="/daily", tags=["daily"])


def _active(db):
    s = (
        db.query(models.InfiniteSession)
        .filter(models.InfiniteSession.status == "active")
        .first()
    )
    if not s:
        raise HTTPException(
            status_code=404, detail="활성 사이클이 없습니다. 먼저 세션을 시작하세요."
        )
    return s


def _validate_fill(action, quantity, price):
    if action not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail=f"action은 buy/sell만 가능합니다: {action}")
    if quantity is None or quantity <= 0:
        raise HTTPException(status_code=400, detail="수량은 0보다 커야 합니다.")
    if price is None or price <= 0:
        raise HTTPException(status_code=400, detail="가격은 0보다 커야 합니다.")


def _seed_alert(t, divisions):
    """시드 소진 임박/도달 알림 (쿼터 손절 타이밍)."""
    if not divisions or divisions <= 0:
        return None
    if t >= divisions:
        return {
            "level": "critical", "turn": round(t, 1), "divisions": divisions,
            "message": f"시드 소진 (T {t:.1f}/{divisions}). 보유 1/4를 손절 매도해 "
                       f"자금을 확보하고 무한매수를 이어가세요.",
        }
    if t >= divisions - 2:
        return {
            "level": "warn", "turn": round(t, 1), "divisions": divisions,
            "message": f"시드 소진 임박 (T {t:.1f}/{divisions}). 곧 1/4 손절로 "
                       f"자금 확보가 필요할 수 있어요.",
        }
    return None


@router.post("/calculate", response_model=schemas.DailyCalcOut)
def calculate(payload: schemas.DailyCalcRequest, db: Session = Depends(get_db)):
    s = _active(db)
    cfg = get_or_create_config(db)
    pos = compute_position(db, s)
    warnings: list[str] = []

    # --- 환율 결정 ---
    if payload.usd_krw_rate:
        rate = float(payload.usd_krw_rate)
    else:
        rate = market.get_usd_krw_rate() if cfg.auto_rate else None
        if not rate:
            rate = float(s.usd_krw_rate or cfg.usd_krw_rate)
            warnings.append("환율 자동조회 실패 → 직전 환율 사용")

    # --- 시세 결정 ---
    price = payload.soxl_price or market.get_stock_close(f"{s.ticker.lower()}.us")
    if not price:
        last = (
            db.query(models.DailyState)
            .filter(models.DailyState.session_id == s.id)
            .order_by(models.DailyState.date.desc())
            .first()
        )
        if last and last.soxl_close:
            price = last.soxl_close
            warnings.append("시세 자동조회 실패 → 직전 종가 사용")
        else:
            warnings.append("시세 조회 실패 → soxl_price 직접 입력 필요")

    avg = pos["avg_price_usd"]
    holding = pos["holding_qty"]
    t = pos["turn_number"]
    base_price = avg if holding > 0 else price  # 첫날은 현재가 기준

    if base_price:
        buy_orders = calc_buy_orders(base_price, t, s.per_turn_usd, rate)
    else:
        buy_orders = []
        warnings.append("기준가 없음 → 매수 계산 불가")

    sell_orders = calc_sell_orders(avg, t, holding, rate, s.target_pct)
    ev = calc_evaluation(holding, avg, pos["remaining_cost_usd"], price or 0, rate)

    the_date = payload.date or date_type.today()

    # --- DailyState upsert ---
    ds = (
        db.query(models.DailyState)
        .filter(models.DailyState.session_id == s.id, models.DailyState.date == the_date)
        .first()
    )
    if not ds:
        ds = models.DailyState(session_id=s.id, date=the_date)
        db.add(ds)
    ds.turn_number = t
    ds.cumulative_quantity = holding
    ds.cumulative_cost_usd = pos["remaining_cost_usd"]
    ds.avg_price_usd = avg
    ds.soxl_close = price
    ds.mode = pos["mode"]
    ds.buy_orders = buy_orders
    ds.sell_orders = sell_orders
    ds.eval_value_usd = ev["eval_value_usd"]
    ds.profit_pct = ev["profit_pct"]
    ds.profit_usd = ev["profit_usd"]
    ds.usd_krw_rate = rate
    ds.eval_value_krw = ev["eval_value_krw"]
    ds.profit_krw = ev["profit_krw"]
    db.commit()

    return schemas.DailyCalcOut(
        session_id=s.id, date=the_date, turn_number=t, mode=pos["mode"],
        usd_krw_rate=rate, soxl_price=price, avg_price_usd=avg, holding_qty=holding,
        buy_orders=buy_orders, sell_orders=sell_orders,
        evaluation=schemas.EvaluationOut(**ev), warnings=warnings,
        seed_alert=_seed_alert(t, s.divisions),
    )


@router.get("/today", response_model=schemas.DailyCalcOut)
def today(db: Session = Depends(get_db)):
    s = _active(db)
    ds = (
        db.query(models.DailyState)
        .filter(
            models.DailyState.session_id == s.id,
            models.DailyState.date == date_type.today(),
        )
        .first()
    )
    if not ds:
        raise HTTPException(
            status_code=404, detail="오늘 계산 내역이 없습니다. /daily/calculate를 먼저 호출하세요."
        )
    return schemas.DailyCalcOut(
        session_id=s.id, date=ds.date, turn_number=ds.turn_number, mode=ds.mode,
        usd_krw_rate=ds.usd_krw_rate or s.usd_krw_rate, soxl_price=ds.soxl_close,
        avg_price_usd=ds.avg_price_usd, holding_qty=int(ds.cumulative_quantity),
        buy_orders=ds.buy_orders or [], sell_orders=ds.sell_orders or [],
        evaluation=schemas.EvaluationOut(
            eval_value_usd=ds.eval_value_usd or 0, profit_usd=ds.profit_usd or 0,
            profit_pct=ds.profit_pct or 0, eval_value_krw=ds.eval_value_krw or 0,
            profit_krw=ds.profit_krw or 0,
        ),
        warnings=[],
        seed_alert=_seed_alert(ds.turn_number, s.divisions),
    )


@router.post("/execute")
def execute(payload: schemas.ExecuteRequest, db: Session = Depends(get_db)):
    s = _active(db)
    inserted = 0
    for f in payload.fills:
        _validate_fill(f.action, f.quantity, f.price_usd)
        db.add(models.Transaction(
            session_id=s.id, date=f.date or date_type.today(),
            action=f.action, order_type=f.order_type,
            quantity=f.quantity, price_usd=f.price_usd,
            total_usd=round(f.quantity * f.price_usd, 2),
            is_executed=True, memo=f.memo,
        ))
        inserted += 1
    db.commit()
    return {"inserted": inserted, "position": compute_position(db, s)}


@router.get("/list")
def list_daily(session_id: int | None = None, db: Session = Depends(get_db)):
    """차트/이력용 — 일자별 상태 + 당일 체결. session_id 없으면 활성 사이클."""
    if session_id is not None:
        s = (
            db.query(models.InfiniteSession)
            .filter(models.InfiniteSession.id == session_id)
            .first()
        )
        if not s:
            raise HTTPException(status_code=404, detail="해당 사이클을 찾을 수 없습니다.")
    else:
        s = _active(db)
    states = (
        db.query(models.DailyState)
        .filter(models.DailyState.session_id == s.id)
        .order_by(models.DailyState.date.asc())
        .all()
    )
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.session_id == s.id,
            models.Transaction.is_executed == True,  # noqa: E712
        )
        .all()
    )
    buy_by, sell_by, fills_by = {}, {}, {}
    for tx in txns:
        bucket = buy_by if tx.action == "buy" else sell_by
        bucket[tx.date] = bucket.get(tx.date, 0) + tx.quantity
        fills_by.setdefault(tx.date, []).append({
            "action": tx.action,
            "quantity": int(round(tx.quantity)),
            "price_usd": tx.price_usd,
            "order_type": tx.order_type,
        })

    points = []
    for ds in states:
        avg = ds.avg_price_usd or 0
        points.append({
            "date": ds.date.isoformat(),
            "soxl_close": ds.soxl_close,
            "avg_price_usd": avg,
            "target_price": round(avg * (1 + s.target_pct / 100.0), 4) if avg else None,
            "turn_number": ds.turn_number,
            "mode": ds.mode,
            "profit_pct": ds.profit_pct,
            "eval_value_krw": ds.eval_value_krw,
            "buy_qty": int(round(buy_by.get(ds.date, 0))),
            "sell_qty": int(round(sell_by.get(ds.date, 0))),
            "fills": fills_by.get(ds.date, []),
        })
    return {"session_id": s.id, "target_pct": s.target_pct, "points": points}


def _tx_dict(t):
    return {
        "id": t.id,
        "date": t.date.isoformat() if t.date else None,
        "action": t.action,
        "order_type": t.order_type,
        "quantity": int(round(t.quantity)),
        "price_usd": t.price_usd,
        "total_usd": t.total_usd,
        "memo": t.memo,
        "is_executed": t.is_executed,
    }


@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db)):
    """활성 사이클의 체결 내역 (최신순)."""
    s = _active(db)
    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.session_id == s.id)
        .order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
        .all()
    )
    return {"transactions": [_tx_dict(t) for t in txns]}


@router.put("/transactions/{tx_id}")
def update_transaction(tx_id: int, payload: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    """체결 내역 수정 — 수정 후 평단·보유 자동 재계산."""
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="해당 체결 내역을 찾을 수 없습니다.")

    action = payload.action if payload.action is not None else tx.action
    quantity = payload.quantity if payload.quantity is not None else tx.quantity
    price = payload.price_usd if payload.price_usd is not None else tx.price_usd
    _validate_fill(action, quantity, price)

    tx.action = action
    tx.quantity = quantity
    tx.price_usd = price
    tx.total_usd = round(quantity * price, 2)
    if payload.date is not None:
        tx.date = payload.date
    if payload.order_type is not None:
        tx.order_type = payload.order_type
    if payload.memo is not None:
        tx.memo = payload.memo
    db.commit()
    db.refresh(tx)

    s = db.query(models.InfiniteSession).filter(models.InfiniteSession.id == tx.session_id).first()
    return {"transaction": _tx_dict(tx), "position": compute_position(db, s) if s else None}


@router.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    """체결 내역 삭제 — 삭제 후 평단·보유 자동 재계산."""
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="해당 체결 내역을 찾을 수 없습니다.")
    sid = tx.session_id
    db.delete(tx)
    db.commit()
    s = db.query(models.InfiniteSession).filter(models.InfiniteSession.id == sid).first()
    return {"deleted": tx_id, "position": compute_position(db, s) if s else None}
