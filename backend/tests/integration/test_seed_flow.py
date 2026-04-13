"""Integration tests for privileged-user seeding."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import scripts.seed as seed_script
from src.core.config import settings
from src.models.user_model import ROLE_ADMIN, ROLE_SECURITY, User
from src.security.jwt import decode_token
from src.security.password import verify_password


def build_seed_env() -> dict[str, str]:
    """Return a deterministic test environment for privileged-user seeding."""
    return {
        "SEED_HIGHER_TIER_USERS": "true",
        "DATABASE_URL": settings.DATABASE_URL,
        "admin_user_username": "seed-admin@example.com",
        "admin_user_password": "SeedAdmin!2026",
        "security_username": "seed-security@example.com",
        "security_password": "SeedSecurity!2026",
    }


async def fetch_users(db_session: AsyncSession) -> list[User]:
    """Load seeded users ordered by email for stable assertions."""
    result = await db_session.execute(select(User).order_by(User.email))
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_seed_script_creates_privileged_users_with_expected_roles(
    db_session: AsyncSession,
) -> None:
    """Verify the seed script inserts both higher-tier users once."""
    env = build_seed_env()

    result = await seed_script.async_main(env=env)

    assert result == 0
    users = await fetch_users(db_session)
    assert [user.email for user in users] == [
        env["admin_user_username"],
        env["security_username"],
    ]
    assert [user.role for user in users] == [ROLE_ADMIN, ROLE_SECURITY]
    assert verify_password(env["admin_user_password"], users[0].hashed_password) is True
    assert verify_password(env["security_password"], users[1].hashed_password) is True


@pytest.mark.asyncio
async def test_seed_script_is_idempotent(
    db_session: AsyncSession,
) -> None:
    """Verify re-running the seeder preserves the original result."""
    env = build_seed_env()

    first_result = await seed_script.async_main(env=env)
    first_users = await fetch_users(db_session)
    first_hashes = {user.email: user.hashed_password for user in first_users}

    second_result = await seed_script.async_main(env=env)
    second_users = await fetch_users(db_session)
    second_hashes = {user.email: user.hashed_password for user in second_users}

    assert first_result == 0
    assert second_result == 0
    assert len(second_users) == 2
    assert second_hashes == first_hashes


@pytest.mark.asyncio
async def test_seeded_users_authenticate_through_the_normal_login_flow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify seeded higher-tier users log in through the public auth API."""
    env = build_seed_env()
    await seed_script.async_main(env=env)

    users = await fetch_users(db_session)
    password_by_email = {
        env["admin_user_username"]: env["admin_user_password"],
        env["security_username"]: env["security_password"],
    }

    for user in users:
        assert verify_password(password_by_email[user.email], user.hashed_password) is True

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": password_by_email[user.email],
            },
        )

        assert response.status_code == 200
        payload = decode_token(response.json()["access_token"])
        assert payload["email"] == user.email
        assert payload["role"] == user.role
