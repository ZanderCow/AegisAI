"""
Shared fixtures for integration tests.

Requires a running PostgreSQL instance at the URL in DATABASE_URL / config.py defaults.
Tables are created once per session via the app lifespan (connect_db) and torn down after.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from src.core.db import engine, Base
import src.models.user_model  # noqa: F401 – ensures User is registered with Base


@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables before the test session and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI ASGI app."""
    from src.main import app  # import here so lifespan runs after tables exist

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def clean_users():
    """Delete all rows from the users table between tests."""
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users"))
