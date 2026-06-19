from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB / CORS
    database_url: str = "sqlite:///./local.db"
    cors_origins: str = "*"

    # 무한매수법 v2.2 기본값
    default_ticker: str = "SOXL"
    default_seed_krw: int = 500_000_000        # 5억
    default_divisions: int = 40                # 40분할
    default_target_pct: float = 20.0           # 평단 +20% 익절
    default_usd_krw_rate: float = 1390.0       # 시작 환율(수정 가능)
    default_version: str = "v2.2"


settings = Settings()
