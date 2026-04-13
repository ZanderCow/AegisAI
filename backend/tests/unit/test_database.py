"""Unit tests for asynchronous database engine and dependency helpers.

This module verifies that the database configuration in ``src.core.database``
creates the expected SQLAlchemy engine and session factory, and that the
``get_db`` dependency correctly yields and tears down async sessions for
FastAPI request handling.
"""
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

import src.core.database as database
from src.core.database_urls import load_database_url, to_sync_database_url
from src.core.config import settings


def test_database_session_maker_uses_configured_engine() -> None:
    """Verify the database engine and session factory use application settings.

    This test confirms that the module-level engine is created from the current
    ``DATABASE_URL`` configuration and that the async session factory is bound
    to that engine with ``expire_on_commit`` disabled for request-scoped usage.
    """
    assert database.engine.url.render_as_string(hide_password=False) == settings.DATABASE_URL
    assert database.async_session_maker.class_ is AsyncSession
    assert database.async_session_maker.kw["bind"] is database.engine
    assert database.async_session_maker.kw["expire_on_commit"] is False


def test_to_sync_database_url_converts_asyncpg_urls() -> None:
    """Verify Alembic-compatible sync URLs are derived from asyncpg URLs."""
    assert (
        to_sync_database_url("postgresql+asyncpg://user:pass@localhost:5432/auth_db")
        == "postgresql+psycopg2://user:pass@localhost:5432/auth_db"
    )


def test_to_sync_database_url_converts_aiosqlite_urls() -> None:
    """Verify SQLite async driver URLs are normalized for sync tooling."""
    assert to_sync_database_url("sqlite+aiosqlite:///./app.db") == "sqlite:///./app.db"


def test_to_sync_database_url_normalizes_postgres_scheme() -> None:
    """Verify legacy ``postgres://`` URLs are normalized for migrations."""
    assert (
        to_sync_database_url("postgres://user:pass@localhost:5432/auth_db")
        == "postgresql+psycopg2://user:pass@localhost:5432/auth_db"
    )


@pytest.mark.parametrize(
    ("raw_url", "expected_url"),
    [
        (
            "postgresql://user:pass@db.railway.internal:5432/auth_db",
            "postgresql+asyncpg://user:pass@db.railway.internal:5432/auth_db",
        ),
        (
            "postgres://user:pass@db.railway.internal:5432/auth_db",
            "postgresql+asyncpg://user:pass@db.railway.internal:5432/auth_db",
        ),
    ],
)
def test_load_database_url_normalizes_standard_postgres_urls(
    monkeypatch: MonkeyPatch,
    raw_url: str,
    expected_url: str,
) -> None:
    """Verify raw Railway/Postgres env URLs are normalized for async startup."""
    monkeypatch.setenv("DATABASE_URL", raw_url)

    assert load_database_url() == expected_url


@pytest.mark.asyncio
async def test_get_db_yields_session_and_closes_context(monkeypatch: MonkeyPatch) -> None:
    """Verify the ``get_db`` dependency yields and closes an async session.

    The dependency is implemented as an async generator backed by an async
    context manager. This test replaces the session factory with a controlled
    mock so the yield and cleanup phases can be asserted directly.

    Args:
        monkeypatch (MonkeyPatch): Pytest fixture used to replace the session
            factory with a deterministic mocked context manager.
    """
    session = Mock(spec=AsyncSession)
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)

    session_maker = Mock(return_value=session_context)
    monkeypatch.setattr(database, "async_session_maker", session_maker)

    session_generator = database.get_db()
    yielded_session = await anext(session_generator)

    assert yielded_session is session
    session_maker.assert_called_once_with()
    session_context.__aenter__.assert_awaited_once()

    await session_generator.aclose()

    session_context.__aexit__.assert_awaited_once()
