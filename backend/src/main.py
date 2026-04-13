"""Application factory and central entry point for the FastAPI project.

This module initializes the FastAPI application, mounts all routers,
and manages application-wide lifecycle events (startup/shutdown).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.config import settings
from src.core.database import engine
from src.core.database_migrations import verify_database_schema_current
from src.api.v1.endpoints import auth
from src.api.v1.endpoints import admin
from src.api.v1.endpoints import chat
from src.api.v1.endpoints import rag
from src.api.v1.endpoints import documents
from src.core.logger import get_logger

logger = get_logger("MAIN")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Event lifecycle context manager handling startup and shutdown routines.
    
    Initializes the database engine and establishes connection pooling upon
    server start. Safely unbinds and disposes open connection resources when 
    the application server terminates.
    
    Args:
        app (FastAPI): The active FastAPI application instance.
    """
    logger.info("Starting up application, connecting to database...")
    if settings.ENVIRONMENT.lower() != "test":
        await verify_database_schema_current(engine, settings.DATABASE_URL)
        logger.info("Database schema matches the current Alembic head revision.")
    yield
    # Safely dispose engine connections immediately upon application shutdown
    logger.info("Shutting down application, disposing database connections...")
    await engine.dispose()

app = FastAPI(
    title="AegisAI API",
    description="Auth and chat endpoints. Use **Authorize** (Bearer token) for `/api/v1/chat/**` after signing up or logging in.",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, str]:
    """Service root — browsers often open `/` first; API routes live under `/api/v1`."""
    return {
        "service": "AegisAI API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "api": "/api/v1",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for Docker and quick manual checks."""
    return {"status": "ok"}


def get_cors_middleware_kwargs() -> dict[str, object]:
    """Build the CORS middleware configuration from environment-backed settings."""
    return {
        "allow_origins": settings.CORS_ALLOWED_ORIGINS,
        # JWT is sent via Authorization headers / localStorage rather than cookies,
        # so credentials support is unnecessary for the current frontend flow.
        "allow_credentials": False,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


app.add_middleware(CORSMiddleware, **get_cors_middleware_kwargs())

app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
