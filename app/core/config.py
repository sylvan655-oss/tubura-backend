from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://tubura_user:yourpassword@localhost:5432/tubura_db"

    # Security
    SECRET_KEY: str = "change-this-to-a-long-random-string-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALGORITHM: str = "HS256"

    # Africa's Talking
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = ""
    AT_SENDER_ID: str = "TUBURA"

    # MTN MoMo
    MTN_MOMO_BASE_URL: str = "https://sandbox.momodeveloper.mtn.com"
    MTN_MOMO_SUBSCRIPTION_KEY: str = ""
    MTN_MOMO_API_USER: str = ""
    MTN_MOMO_API_KEY: str = ""
    MTN_MOMO_ENVIRONMENT: str = "sandbox"

    # Airtel Money
    AIRTEL_BASE_URL: str = "https://openapi.airtel.africa"
    AIRTEL_CLIENT_ID: str = ""
    AIRTEL_CLIENT_SECRET: str = ""
    AIRTEL_ENVIRONMENT: str = "sandbox"

    # App
    APP_ENV: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Admin dashboard (/admin) login — change these in production!
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-this-password"

    # OTP
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5


settings = Settings()
