"""Unit tests for application startup lifecycle behavior."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import src.main as main


@pytest.mark.asyncio
async def test_lifespan_creates_tables_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify startup bootstraps schema when auto-create is enabled."""
    conn = Mock()
    conn.run_sync = AsyncMock(return_value=None)

    engine_context = MagicMock()
    engine_context.__aenter__ = AsyncMock(return_value=conn)
    engine_context.__aexit__ = AsyncMock(return_value=None)

    fake_engine = Mock()
    fake_engine.begin.return_value = engine_context
    fake_engine.dispose = AsyncMock(return_value=None)

    fake_logger = Mock()

    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(AUTO_CREATE_TABLES=True, ENVIRONMENT="development"),
    )
    monkeypatch.setattr(main, "engine", fake_engine)
    monkeypatch.setattr(main, "logger", fake_logger)

    async with main.lifespan(main.app):
        pass

    fake_engine.begin.assert_called_once_with()
    conn.run_sync.assert_awaited_once_with(main.Base.metadata.create_all)
    fake_engine.dispose.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_lifespan_skips_table_creation_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify production-style startup skips schema mutation."""
    fake_engine = Mock()
    fake_engine.dispose = AsyncMock(return_value=None)
    fake_logger = Mock()

    monkeypatch.setattr(
        main,
        "settings",
        SimpleNamespace(AUTO_CREATE_TABLES=False, ENVIRONMENT="production"),
    )
    monkeypatch.setattr(main, "engine", fake_engine)
    monkeypatch.setattr(main, "logger", fake_logger)

    async with main.lifespan(main.app):
        pass

    fake_engine.begin.assert_not_called()
    fake_engine.dispose.assert_awaited_once_with()
    fake_logger.info.assert_any_call(
        "Automatic schema creation is disabled for environment '%s'.",
        "production",
    )


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
