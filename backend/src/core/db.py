from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=True)

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
    # Import here to avoid circular imports at module load time
    from models import user_model  # noqa: F401 – registers User with Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def disconnect_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    await engine.dispose()