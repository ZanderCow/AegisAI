"""
User Repository (repo/user_repository.py)
Handles all database operations for the User model.
Depends on: SQLAlchemy async session (from core/db.py), User model (from models/user_model.py)
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.user_model import User
from src.core.logger import get_logger

auth_logger = get_logger("auth")

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Fetch a user by email address.
        Returns the User object or None if not found.
        """
        auth_logger.info(f"[AUTH][REPO] Querying database for user by email")
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()
        if user:
            auth_logger.info("[AUTH][REPO] User record retrieved successfully")
        else:
            auth_logger.info(f"[AUTH][REPO] No user found for email {email}")
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Fetch a user by their primary key ID.
        Returns the User object or None if not found.
        """
        auth_logger.info(f"[AUTH][REPO] Querying database for user by ID")
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if user:
            auth_logger.info("[AUTH][REPO] User record retrieved successfully")
        else:
            auth_logger.info(f"[AUTH][REPO] No user found for ID {user_id}")
        return user

    async def create_user(self, email: str, hashed_password: str) -> User:
        """
        Insert a new user into the database.
        Returns the created User object with its generated ID.
        """
        auth_logger.info("[AUTH][REPO] Inserting new user record into database")
        new_user = User(email=email, hashed_password=hashed_password)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)  # Populates auto-generated fields like id
        auth_logger.info("[AUTH][REPO] New user record inserted successfully")
        return new_user