"""
main.py
=======
Application entry point for the FastAPI backend.

This module creates the ``FastAPI`` application instance, registers a
**lifespan** context manager for startup / shutdown hooks, and includes
all API routers.

Running Locally
---------------
.. code-block:: bash

    uvicorn src.main:app --reload

The ``--reload`` flag enables auto-restart on file changes during development.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from src.database import Base, engine
from src.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application-wide startup and shutdown tasks.

    Startup
        Creates all database tables that do not yet exist.  This is a
        convenience for development; production deployments should use a
        migration tool such as **Alembic**.

    Shutdown
        Disposes of the async engine, releasing every pooled connection
        back to PostgreSQL.
    """
    # ── Startup ─────────────────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Application runs here

    # ── Shutdown ────────────────────────────────────────────────────────
    await engine.dispose()


app = FastAPI(
    title="Backend API",
    description="A production-quality REST API built with FastAPI and PostgreSQL.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Register Routers ────────────────────────────────────────────────────────

app.include_router(users_router)
