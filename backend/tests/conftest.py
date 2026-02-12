"""
conftest.py
===========
Shared pytest fixtures for **development** integration tests.

These fixtures connect to a **real PostgreSQL** database using the
``DATABASE_URL`` environment variable (or ``.env`` file).  They create
all tables at the start of the test session and drop them at the end,
so every run starts from a clean slate.

.. warning::

    These tests generate fake data and are intended for **local
    development only**.  They must **not** be executed in production
    because they will create and destroy tables in the target database.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.database import Base, Settings, get_session
from src.main import app


# ── Load Settings ───────────────────────────────────────────────────────────

_settings = Settings()  # type: ignore[call-arg]

# ── Test Engine & Session Factory ───────────────────────────────────────────

_test_engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="function", autouse=True)
async def _setup_database() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop them afterwards.

    This ensures every test starts with a clean database and avoids
    session-scoped event loop closure issues.
    """
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await _test_engine.dispose()


@pytest.fixture()
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh ``AsyncSession`` for a single test function.

    The session is closed automatically after the test completes.
    """
    async with _test_session_factory() as session:
        yield session


@pytest.fixture()
async def client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an ``httpx.AsyncClient`` wired to the FastAPI application.

    The ``get_session`` dependency is overridden so that the application
    uses the same ``AsyncSession`` created by the ``async_session``
    fixture.  This keeps every test isolated and deterministic.
    """

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
