"""Seed higher-tier users through the backend ORM and auth utilities."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
import sys
from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.user_model import ROLE_ADMIN, ROLE_SECURITY
from src.core.database_urls import normalize_async_database_url
from src.service.seed_service import SeedService, SeedUserRequest, SeedUserResult

SEED_FLAG_ENV = "SEED_HIGHER_TIER_USERS"
DATABASE_URL_ENV = "DATABASE_URL"

logger = logging.getLogger("seed")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    )


def is_seeding_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Return True when privileged-user seeding is explicitly enabled."""
    active_env = env if env is not None else os.environ
    return active_env.get(SEED_FLAG_ENV) == "true"


def require_env(env: Mapping[str, str], name: str) -> str:
    """Fetch a required environment variable and reject blank values."""
    value = env.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_seed_requests(env: Mapping[str, str]) -> list[SeedUserRequest]:
    """Resolve privileged-user inputs from environment variables."""
    return [
        SeedUserRequest(
            email=require_env(env, "admin_user_username"),
            password=require_env(env, "admin_user_password"),
            role=ROLE_ADMIN,
            label="admin",
        ),
        SeedUserRequest(
            email=require_env(env, "security_username"),
            password=require_env(env, "security_password"),
            role=ROLE_SECURITY,
            label="security",
        ),
    ]


async def seed_higher_tier_users(
    session_factory: async_sessionmaker[AsyncSession],
    env: Mapping[str, str] | None = None,
) -> list[SeedUserResult]:
    """Run the idempotent privileged-user seed against the database."""
    active_env = env if env is not None else os.environ
    requests = build_seed_requests(active_env)

    async with session_factory() as session:
        service = SeedService(session)
        return await service.seed_users(requests)


async def async_main(env: Mapping[str, str] | None = None) -> int:
    """Entrypoint used by the CLI and tests."""
    active_env = env if env is not None else os.environ
    if not is_seeding_enabled(active_env):
        logger.info(
            "%s is not true; skipping privileged-user seeding.",
            SEED_FLAG_ENV,
        )
        return 0

    try:
        database_url = normalize_async_database_url(
            require_env(active_env, DATABASE_URL_ENV)
        )
        build_seed_requests(active_env)
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        results = await seed_higher_tier_users(session_factory, env=active_env)
    except Exception as exc:  # noqa: BLE001 - CLI should surface unexpected failures
        logger.exception("Privileged-user seeding failed: %s", exc)
        return 1
    finally:
        await engine.dispose()

    for result in results:
        logger.info(
            "Seed %s: %s user %s",
            result.status,
            result.role,
            result.email,
        )

    return 0


def main() -> int:
    """Synchronous wrapper for CLI execution."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
