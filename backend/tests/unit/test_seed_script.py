"""Unit tests for the privileged-user seed script."""
from unittest.mock import AsyncMock, Mock

import pytest

import scripts.seed as seed_script
import src.service.seed_service as seed_service


@pytest.mark.asyncio
async def test_async_main_noops_when_higher_tier_seeding_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify disabled seeding exits before any database work begins."""
    create_engine_mock = Mock()
    hash_password_mock = Mock()

    monkeypatch.setattr(seed_script, "create_async_engine", create_engine_mock)
    monkeypatch.setattr(seed_service, "hash_password", hash_password_mock)

    result = await seed_script.async_main(env={})

    assert result == 0
    create_engine_mock.assert_not_called()
    hash_password_mock.assert_not_called()


@pytest.mark.asyncio
async def test_async_main_fails_fast_when_required_seed_env_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify enabled seeding rejects missing credential variables clearly."""
    create_engine_mock = Mock()
    seed_users_mock = AsyncMock()

    monkeypatch.setattr(seed_script, "create_async_engine", create_engine_mock)
    monkeypatch.setattr(seed_script, "seed_higher_tier_users", seed_users_mock)

    result = await seed_script.async_main(
        env={
            "SEED_HIGHER_TIER_USERS": "true",
            "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@db:5432/auth_db",
        }
    )

    assert result == 1
    create_engine_mock.assert_not_called()
    seed_users_mock.assert_not_called()
