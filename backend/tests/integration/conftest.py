"""Shared pytest fixtures for all integration tests.

Centralizes the test database engine, dependency override, and the
setup/teardown fixture so all test modules share a single DB engine
and override — preventing test_auth.py and test_chat.py from clobbering
each other's app.dependency_overrides at module-import time.
"""
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.database import get_db
from src.main import app
import src.models.conversation_model  # noqa: F401 — registers Conversation+Message with Base
from src.models.user_model import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncIterator[AsyncSession]:
    """Yield the shared in-memory database session for integration tests.

    Yields:
        AsyncSession: A session connected to the isolated SQLite test engine.
    """
    async with TestingSessionLocal() as session:
        yield session


# Set once here — test modules must NOT set this themselves
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncIterator[None]:
    """Recreate the database schema around each integration test.

    Yields:
        None: Control back to the active test once tables are ready.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an HTTP client wired directly to the FastAPI ASGI app.

    Yields:
        AsyncClient: A test client configured with the application's ASGI transport.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
