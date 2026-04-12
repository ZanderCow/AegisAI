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

    monkeypatch.setattr(main, "engine", fake_engine)
    monkeypatch.setattr(main, "logger", fake_logger)

    # Lifespan should log startup, yield, then dispose engine on exit
    async with main.lifespan(main.app):
        fake_logger.info.assert_any_call("Starting up application, connecting to database...")

    # Verification of shutdown cleanup
    fake_logger.info.assert_any_call("Shutting down application, disposing database connections...")
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
