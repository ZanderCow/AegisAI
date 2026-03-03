"""Asynchronous database connection management and setup.

This module establishes the underlying connection to the PostgreSQL
database via SQLAlchemy 2.0 and provides dependency injection utilities
for acquiring async sessions in FastAPI endpoints.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.core.config import settings

# Global async database engine created from the configuration URL
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Session factory for generating independent asynchronous transactional sessions
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding asynchronous database sessions.
    
    This generator yields an active `AsyncSession` to the caller and ensures
    that the session is cleanly closed once the request context concludes.
    
    Yields:
        AsyncSession: An async SQLAlchemy database session.
    """
    async with async_session_maker() as session:
        yield session
