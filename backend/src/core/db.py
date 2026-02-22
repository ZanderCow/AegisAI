from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings
from .logger import get_logger


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.should_echo_sql,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def connect_db() -> None:
    """Create all database tables on startup."""
    db_logger = get_logger("db")
    db_logger.info("[DB][SETUP] Initializing database connection...")

    if settings.should_auto_create_tables:
        # Import here to avoid circular imports at module load time
        from src.models import user_model  # noqa: F401 – registers User with Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        db_logger.info("[DB][SETUP] Database successfully connected and tables verified")
    else:
        db_logger.info("[DB][SETUP] AUTO_CREATE_TABLES disabled; skipping create_all")


async def disconnect_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    db_logger = get_logger("db")
    db_logger.info("[DB][SETUP] Disconnecting database...")
    await engine.dispose()
    db_logger.info("[DB][SETUP] Database disconnected successfully")
