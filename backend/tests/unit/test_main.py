"""Unit tests for application startup lifecycle behavior."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import src.main as main


@pytest.mark.asyncio
async def test_lifespan_manages_engine_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify startup and shutdown routines manage the database engine correctly."""
    fake_engine = Mock()
    fake_engine.dispose = AsyncMock(return_value=None)
    fake_logger = Mock()
    fake_verify_database_schema_current = AsyncMock(return_value=None)

    monkeypatch.setattr(main, "engine", fake_engine)
    monkeypatch.setattr(main, "logger", fake_logger)
    monkeypatch.setattr(main, "verify_database_schema_current", fake_verify_database_schema_current)
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            ENVIRONMENT="development",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@db:5432/auth_db",
            CORS_ALLOWED_ORIGINS=["http://localhost:5173"],
        ),
    )

    # Lifespan should log startup, yield, then dispose engine on exit
    async with main.lifespan(main.app):
        fake_logger.info.assert_any_call("Starting up application, connecting to database...")
        fake_logger.info.assert_any_call("Database schema matches the current Alembic head revision.")

    # Verification of shutdown cleanup
    fake_logger.info.assert_any_call("Shutting down application, disposing database connections...")
    fake_verify_database_schema_current.assert_awaited_once_with(
        fake_engine,
        "postgresql+asyncpg://postgres:postgres@db:5432/auth_db",
    )
    fake_engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_lifespan_skips_schema_verification_in_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify schema revision checks are skipped for the test environment."""
    fake_engine = Mock()
    fake_engine.dispose = AsyncMock(return_value=None)
    fake_logger = Mock()
    fake_verify_database_schema_current = AsyncMock(return_value=None)

    monkeypatch.setattr(main, "engine", fake_engine)
    monkeypatch.setattr(main, "logger", fake_logger)
    monkeypatch.setattr(main, "verify_database_schema_current", fake_verify_database_schema_current)
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(
            ENVIRONMENT="test",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@db:5432/auth_db",
            CORS_ALLOWED_ORIGINS=["http://localhost:5173"],
        ),
    )

    async with main.lifespan(main.app):
        fake_logger.info.assert_any_call("Starting up application, connecting to database...")

    fake_verify_database_schema_current.assert_not_called()
    fake_engine.dispose.assert_awaited_once_with()


def test_get_cors_middleware_kwargs_uses_settings_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify FastAPI CORS middleware is driven by configured browser origins."""
    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(CORS_ALLOWED_ORIGINS=["http://localhost:5173"]),
    )

    assert main.get_cors_middleware_kwargs() == {
        "allow_origins": ["http://localhost:5173"],
        "allow_credentials": False,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
