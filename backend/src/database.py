"""
database.py
===========
Centralised async database configuration for the application.

Responsibilities
----------------
* Load the ``DATABASE_URL`` from environment variables via **pydantic-settings**.
* Create a single ``AsyncEngine`` (backed by **asyncpg**) with sensible
  connection-pool defaults.
* Provide an ``async_sessionmaker`` factory that produces ``AsyncSession``
  instances bound to the engine.
* Expose a FastAPI-compatible dependency – ``get_session()`` – that yields one
  ``AsyncSession`` per request and guarantees cleanup afterwards.

Usage
-----
Import ``get_session`` in your routers and declare it as a FastAPI dependency::

    from src.database import get_session

    @router.get("/items")
    async def list_items(session: AsyncSession = Depends(get_session)):
        ...

Notes
-----
* ``expire_on_commit=False`` prevents SQLAlchemy from issuing implicit lazy
  loads after a commit, which would fail inside an async context.
* ``pool_pre_ping=True`` lets the pool transparently replace stale connections.
"""

from collections.abc import AsyncGenerator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# ── Settings ────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Application settings populated from environment variables.

    Pydantic-settings reads a ``.env`` file (if present) and merges the
    values with real environment variables.  The ``DATABASE_URL`` variable
    is required – the application will refuse to start without it.
    """

    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore[call-arg]


# ── Engine & Session Factory ────────────────────────────────────────────────


engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
"""Global async engine instance – one per process."""


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
"""Factory that produces fresh ``AsyncSession`` objects."""


# ── ORM Base ────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Declarative base class inherited by every ORM model in the project."""

    pass


# ── FastAPI Dependency ──────────────────────────────────────────────────────


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` scoped to a single request.

    The session is automatically closed when the request finishes,
    regardless of whether it succeeded or raised an exception.
    """
    async with async_session_factory() as session:
        yield session