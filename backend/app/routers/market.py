from fastapi import APIRouter

from app.services import market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/check")
def check():
    """환율·SOXL 시세 자동조회 진단 (소스별 성공/실패)."""
    return market.check("SOXL")


@router.get("/snapshot")
def snapshot():
    return market.get_market_snapshot("SOXL")
