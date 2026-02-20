import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_model import User


class UserRepository:
    """
    Repository layer for User database operations.
    Handles all interactions with the PostgreSQL database via SQLAlchemy async sessions.
    """

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch a user by their UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Fetch a user by their unique email address."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, user: User) -> User:
        """
        Persist a new user to the database.
        Note: The user object must have `email` and `hashed_password` populated.
        """
        session.add(user)
        # We need to flush or commit, usually flush so that the ID is generated
        # and it remains in the same transaction for the service layer to control.
        await session.flush()
        await session.refresh(user)
        return user
