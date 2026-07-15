from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Required ──────────────────────────────────────────────────────────
    DATABASE_URL: str
    SECRET_KEY: str = "change-me-in-production"

    # ── First admin (used by seed.py and the /admin backdoor) ────────────
    TAX_RATE: float = 0.0                     # off for now; set e.g. 0.18 in Railway to enable VAT
    DELIVERY_FEE_SAME_DISTRICT: int = 1000    # RWF
    DELIVERY_FEE_SAME_PROVINCE: int = 2000
    DELIVERY_FEE_OTHER: int = 3000
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me"

    # ── Africa's Talking SMS (optional — SMS is skipped if missing) ──────
    AT_USERNAME: str = ""
    AT_API_KEY: str = ""
    AT_SENDER: str = ""

    # ── Misc ──────────────────────────────────────────────────────────────
    APP_ENV: str = "development"          # development | production
    CORS_ORIGINS: str = "*"               # comma-separated list, or *
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30   # 30 days

    class Config:
        env_file = ".env"
        extra = "ignore"   # ignore any leftover env vars from the old app

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """Railway gives postgresql://; psycopg3 wants postgresql+psycopg://."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
