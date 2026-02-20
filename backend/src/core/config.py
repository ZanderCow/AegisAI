from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AegisAI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://test_admin:test_password@localhost:5433/aegis_test_db"

    # JWT
    secret_key: str = "CHANGE_ME_use_openssl_rand_hex_32_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS — in .env use a JSON array: CORS_ORIGINS=["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
