"""
Core Configuration (core/config.py)
Loads environment variables and exposes app settings via a Settings object.
Requires: pip install pydantic-settings python-dotenv
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # -----------------------------------------------------------------------
    # App
    # -----------------------------------------------------------------------
    APP_NAME: str = "AegisAI"
    DEBUG: bool = False

    # -----------------------------------------------------------------------
    # JWT
    # -----------------------------------------------------------------------
    SECRET_KEY: str = "change-this-to-a-long-random-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/aegisai"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — reads .env file once at startup."""
    return Settings()


# Module-level singleton for direct imports: from core.config import settings
settings = get_settings()