"""Repository layer for database operations concerning Users.

This module isolates the actual SQLAlchemy ORM queries from the rest of
the application, conforming to the layered architecture pattern.
"""
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

    async def get_by_id(self, user_id: str) -> User | None:
        """Retrieves a single user by their UUID.

        Args:
            user_id: The UUID string of the user.

        Returns:
            User | None: The matching User model if found, otherwise None.
        """
        result = await self.session.execute(select(User).where(User.id == uuid.UUID(user_id)))
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

    async def create_user(self, email: str, hashed_password: str, role: str = "it") -> User:
        """Inserts a new user record into the database.

        Args:
            email (str): The new user's email address.
            hashed_password (str): The pre-hashed password string.
            role (str): The user's role. Defaults to 'it'.

        Returns:
            User: The newly created User model including the generated database ID.

        Raises:
            SQLAlchemyError: If there is an issue executing the database query or commit.
        """
        logger.info(f"Creating new user with email: {email}, role: {role}")
        db_user = User(email=email, hashed_password=hashed_password, role=role)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        logger.info(f"Successfully created user with ID: {db_user.id}")
        return db_user
