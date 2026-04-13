"""Shared pytest fixtures for all integration tests.

These fixtures exercise the app against the same Docker-backed PostgreSQL
database configured for the ``backend-test`` service. A dedicated test engine
is built from ``settings.DATABASE_URL`` so requests and direct DB assertions
use the same containerized database while remaining isolated from the app's
module-global engine pool.
"""
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.main import app
from src.core.config import settings
from src.core.database import get_db
from src.models.registry import Base

TEST_DATABASE_URL = settings.DATABASE_URL

# pytest-asyncio uses a fresh event loop per test. NullPool prevents asyncpg
# connections created in one loop from being reused in another.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)
TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncIterator[AsyncSession]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncIterator[None]:
    """Creates all tables before each test and drops them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide direct DB access backed by the Docker test database."""
    async with TestingSessionLocal() as session:
        yield session
