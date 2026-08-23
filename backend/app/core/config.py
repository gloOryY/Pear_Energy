from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Pear Energy API"
    ENV: str = "dev"
    DEBUG: bool = True

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "chargepoint"
    POSTGRES_PASSWORD: str = "chargepoint_dev"
    POSTGRES_DB: str = "chargepoint"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "CHANGE_ME_super_secret_key_min_32_chars_long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MIN: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost"
    RATE_LIMIT_AUTH_PER_MIN: int = 10

    PAYMENT_PROVIDER: str = "mock"
    PAYMENT_WEBHOOK_SECRET: str = "mock-webhook-secret"
    PLATFORM_COMMISSION_PERCENT: float = 10.0

    STATION_MODE: str = "mock"  # mock | http

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
