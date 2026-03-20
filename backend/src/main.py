"""Application factory and central entry point for the FastAPI project.

This module initializes the FastAPI application, mounts all routers,
and manages application-wide lifecycle events (startup/shutdown).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.database import engine
from src.models.user_model import Base
from src.models import conversation_model as _conversation_model  # noqa: F401
from src.api.v1.endpoints import auth
from src.api.v1.endpoints import chat
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
    async with engine.begin() as conn:
        # Note: In a production enterprise app this is generally handled by Alembic schema migrations
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
    yield
    # Safely dispose engine connections immediately upon application shutdown
    logger.info("Shutting down application, disposing database connections...")
    await engine.dispose()

app = FastAPI(title="Authentication API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
