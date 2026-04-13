"""Database URL helpers shared by runtime and migration tooling."""
from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class DatabaseUrlSettings(BaseSettings):
    """Minimal settings required to load the application database URL."""

    DATABASE_URL: str = Field(
        ...,
        description="Application database connection string.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_database_url() -> str:
    """Load the database URL without depending on full application settings."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return normalize_async_database_url(database_url)

    return normalize_async_database_url(DatabaseUrlSettings().DATABASE_URL)


def normalize_async_database_url(database_url: str) -> str:
    """Normalize standard PostgreSQL URLs for async SQLAlchemy usage."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return database_url


def to_sync_database_url(database_url: str) -> str:
    """Convert async-friendly URLs into sync URLs for migration tooling."""
    normalized = database_url
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)

    url = make_url(normalized)
    driver_overrides = {
        "postgresql": "postgresql+psycopg2",
        "postgresql+asyncpg": "postgresql+psycopg2",
        "sqlite+aiosqlite": "sqlite",
    }
    drivername = driver_overrides.get(url.drivername, url.drivername)
    return url.set(drivername=drivername).render_as_string(hide_password=False)
