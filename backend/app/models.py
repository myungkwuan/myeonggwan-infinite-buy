from datetime import datetime, date as date_type

from sqlalchemy import (
    Column, Integer, String, Float, BigInteger, Date, DateTime,
    Boolean, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class InfiniteSession(Base):
    """사이클(세션) 정보 — 하나의 무한매수 사이클."""
    __tablename__ = "infinite_sessions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, default="SOXL")
    seed_krw = Column(BigInteger, nullable=False)
    seed_usd = Column(Float, nullable=False)
    divisions = Column(Integer, nullable=False, default=40)
    per_turn_usd = Column(Float, nullable=False)          # 회당 매수액 = seed_usd / divisions (세션 시작 시 USD 고정)
    target_pct = Column(Float, nullable=False, default=20.0)
    version = Column(String, nullable=False, default="v2.2")
    usd_krw_rate = Column(Float, nullable=False, default=1390.0)  # 세션 시작 환율(시드 환산 기준)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")  # active / completed / quartered

    final_profit_pct = Column(Float, nullable=True)
    final_profit_krw = Column(BigInteger, nullable=True)
    total_turns = Column(Float, nullable=True)             # 종료 시점 T값
    memo = Column(String, nullable=True)

    daily_states = relationship(
        "DailyState", back_populates="session", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="session", cascade="all, delete-orphan"
    )


class DailyState(Base):
    """매일 계산된 상태 + 당일 주문(LOC) 스냅샷."""
    __tablename__ = "daily_states"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("infinite_sessions.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, default=date_type.today)
    turn_number = Column(Float, nullable=False)            # T값 (연속값)

    cumulative_quantity = Column(Float, nullable=False, default=0.0)
    cumulative_cost_usd = Column(Float, nullable=False, default=0.0)
    avg_price_usd = Column(Float, nullable=False, default=0.0)

    soxl_close = Column(Float, nullable=True)
    mode = Column(String, nullable=False)                 # 전반전 / 후반전 / 쿼터

    buy_orders = Column(JSON, nullable=True)              # [{label,order_type,quantity,price_usd,amount_usd,amount_krw,note}]
    sell_orders = Column(JSON, nullable=True)

    eval_value_usd = Column(Float, nullable=True)
    profit_pct = Column(Float, nullable=True)
    profit_usd = Column(Float, nullable=True)

    # --- [추가] 환율 자동조회 + 원화 병기 표시용 ---
    usd_krw_rate = Column(Float, nullable=True)           # [추가] 당일 적용 환율
    eval_value_krw = Column(BigInteger, nullable=True)    # [추가] 평가액(원화)
    profit_krw = Column(BigInteger, nullable=True)        # [추가] 평가손익(원화)

    session = relationship("InfiniteSession", back_populates="daily_states")
    transactions = relationship("Transaction", back_populates="daily_state")


class Transaction(Base):
    """실제 체결 내역 (사용자가 키움에서 체결 후 입력)."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("infinite_sessions.id"), nullable=False, index=True
    )
    daily_state_id = Column(
        Integer, ForeignKey("daily_states.id"), nullable=True, index=True
    )
    date = Column(Date, nullable=False, default=date_type.today)
    turn_number = Column(Float, nullable=True)

    action = Column(String, nullable=False)               # buy / sell
    order_type = Column(String, nullable=True)            # LOC / MOC / 지정가

    quantity = Column(Float, nullable=False)
    price_usd = Column(Float, nullable=False)
    total_usd = Column(Float, nullable=False)
    is_executed = Column(Boolean, nullable=False, default=False)
    memo = Column(String, nullable=True)

    session = relationship("InfiniteSession", back_populates="transactions")
    daily_state = relationship("DailyState", back_populates="transactions")


class AppConfig(Base):
    """앱 전역 설정 (싱글톤 id=1) — 기본 시드/분할/익절/환율, 자동조회 on/off."""
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True)            # 항상 1
    ticker = Column(String, nullable=False, default="SOXL")
    seed_krw = Column(BigInteger, nullable=False, default=500_000_000)
    divisions = Column(Integer, nullable=False, default=40)
    target_pct = Column(Float, nullable=False, default=20.0)
    usd_krw_rate = Column(Float, nullable=False, default=1390.0)   # 직전/수동 환율
    auto_rate = Column(Boolean, nullable=False, default=True)      # 환율 자동조회 on/off
    version = Column(String, nullable=False, default="v2.2")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
