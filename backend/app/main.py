from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (테이블 등록)
from app.routers import session as session_router
from app.routers import daily as daily_router
from app.routers import config as config_router
from app.routers import market as market_router
from app.routers import stats as stats_router
from app.routers import backup as backup_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 0~1: 개발 편의용 자동 테이블 생성 (운영은 Alembic 권장)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="명관 무한매수법 API",
    description="라오어 무한매수법 v2.2 자동 계산 (SOXL)",
    version="0.2.0",
    lifespan=lifespan,
)

origins = (
    ["*"]
    if settings.cors_origins == "*"
    else [o.strip() for o in settings.cors_origins.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router.router, prefix=API_PREFIX)
app.include_router(daily_router.router, prefix=API_PREFIX)
app.include_router(config_router.router, prefix=API_PREFIX)
app.include_router(market_router.router, prefix=API_PREFIX)
app.include_router(stats_router.router, prefix=API_PREFIX)
app.include_router(backup_router.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"app": "명관 무한매수법", "version": "v2.2", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
