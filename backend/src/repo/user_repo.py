"""Repository layer for database operations concerning Users.

This module isolates the actual SQLAlchemy ORM queries from the rest of
the application, conforming to the layered architecture pattern.
"""
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.user_model import User
from src.core.logger import get_logger

logger = get_logger("USER_REPOSITORY")

class UserRepository:
    """Repository handling all CRUD interactions for the User database model.
    
    Attributes:
        session (AsyncSession): The active async SQLAlchemy session to execute queries.
    """
    def __init__(self, session: AsyncSession) -> None:
        """Initializes the repository with a database session.
        
        Args:
            session (AsyncSession): The active async SQLAlchemy session to execute queries.
        """
        self.session = session

    @staticmethod
    def _normalize_user_id(user_id: str | uuid.UUID) -> uuid.UUID:
        return user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(user_id)

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        """Retrieves a single user by their UUID.

        Args:
            user_id: The UUID string of the user.

        Returns:
            User | None: The matching User model if found, otherwise None.
        """
        result = await self.session.execute(select(User).where(User.id == self._normalize_user_id(user_id)))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a single user by their email address.
        
        Args:
            email (str): The email address to search for.
            
        Returns:
            User | None: The matching User model if found, otherwise None.
            
        Raises:
            SQLAlchemyError: If there is an issue executing the database query.
        """
        logger.info(f"Retrieving user by email: {email}")
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if user:
            logger.info(f"User found: {user.id}")
        else:
            logger.info("User not found")
        return user

    async def list_all(self) -> list[User]:
        """Return every user ordered for stable admin-table display."""
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc(), User.email.asc())
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        role: str = "user",
        full_name: str | None = None,
    ) -> User:
        """Inserts a new user record into the database.

        Args:
            email (str): The new user's email address.
            hashed_password (str): The pre-hashed password string.
            role (str): The user's role. Defaults to 'user'.
            full_name (str | None): Optional display name for the user.

        Returns:
            User: The newly created User model including the generated database ID.

        Raises:
            SQLAlchemyError: If there is an issue executing the database query or commit.
        """
        logger.info(f"Creating new user with email: {email}, role: {role}")
        db_user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        logger.info(f"Successfully created user with ID: {db_user.id}")
        return db_user

    async def update_role(self, user_id: str | uuid.UUID, role: str) -> User | None:
        """Persist a role change and return the updated user."""
        db_user = await self.get_by_id(user_id)
        if db_user is None:
            return None

        db_user.role = role
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def update_last_login(
        self,
        user_id: str | uuid.UUID,
        last_login: datetime,
    ) -> User | None:
        """Persist the user's most recent login timestamp."""
        db_user = await self.get_by_id(user_id)
        if db_user is None:
            return None

        db_user.last_login = last_login
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: str | uuid.UUID) -> bool:
        """Hard delete a user by id."""
        db_user = await self.get_by_id(user_id)
        if db_user is None:
            return False

        await self.session.delete(db_user)
        await self.session.commit()
        return True
