from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    ticker: Optional[str] = None
    seed_krw: Optional[int] = None        # None이면 config 기본값(5억)
    divisions: Optional[int] = None
    target_pct: Optional[float] = None
    usd_krw_rate: Optional[float] = None  # None이면 자동조회
    soxl_price: Optional[float] = None    # 참고용 시작가
    memo: Optional[str] = None


class SessionOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    ticker: str
    seed_krw: int
    seed_usd: float
    divisions: int
    per_turn_usd: float
    target_pct: float
    version: str
    usd_krw_rate: float
    status: str
    started_at: datetime


class OrderOut(BaseModel):
    label: str
    order_type: str
    quantity: int
    price_usd: Optional[float] = None
    amount_usd: Optional[float] = None
    amount_krw: Optional[int] = None
    note: str = ""


class EvaluationOut(BaseModel):
    eval_value_usd: float
    profit_usd: float
    profit_pct: float
    eval_value_krw: int
    profit_krw: int


class DailyCalcRequest(BaseModel):
    soxl_price: Optional[float] = None
    usd_krw_rate: Optional[float] = None
    date: Optional[date_type] = None


class DailyCalcOut(BaseModel):
    session_id: int
    date: date_type
    turn_number: float
    mode: str
    usd_krw_rate: float
    soxl_price: Optional[float] = None
    avg_price_usd: float
    holding_qty: int
    buy_orders: list[OrderOut]
    sell_orders: list[OrderOut]
    evaluation: EvaluationOut
    warnings: list[str] = []
    seed_alert: Optional[dict] = None


class FillIn(BaseModel):
    action: str            # buy / sell
    quantity: float
    price_usd: float
    order_type: Optional[str] = None
    date: Optional[date_type] = None
    memo: Optional[str] = None


class ExecuteRequest(BaseModel):
    fills: list[FillIn]


class ConfigOut(BaseModel):
    model_config = {"from_attributes": True}
    ticker: str
    seed_krw: int
    divisions: int
    target_pct: float
    usd_krw_rate: float
    auto_rate: bool
    version: str


class ConfigUpdate(BaseModel):
    ticker: Optional[str] = None
    seed_krw: Optional[int] = None
    divisions: Optional[int] = None
    target_pct: Optional[float] = None
    usd_krw_rate: Optional[float] = None
    auto_rate: Optional[bool] = None


class TransactionUpdate(BaseModel):
    action: Optional[str] = None
    quantity: Optional[float] = None
    price_usd: Optional[float] = None
    date: Optional[date_type] = None
    order_type: Optional[str] = None
    memo: Optional[str] = None
