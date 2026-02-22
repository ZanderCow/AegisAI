"""
Service Layer (service/user_service.py)
Business logic for user authentication.
"""
import uuid

from fastapi import HTTPException, status

from src.security.password import hash_password, verify_password
from src.security.jwt import create_access_token, decode_access_token
from src.repo.user_repository import UserRepository
from src.models.user_model import User
from src.core.logger import get_logger

auth_logger = get_logger("auth")

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repo = user_repository

    async def register_user(self, email: str, password: str) -> tuple[User, str]:
        """
        Register a new user.
        - Checks if email exists
        - Hashes password
        - Creates user via repository
        - Returns (user, jwt_token) tuple — token issued immediately on registration
        """
        auth_logger.info("[AUTH][SERVICE] Auth service activated — processing registration")
        existing_user = await self.repo.get_user_by_email(email)
        if existing_user:
            auth_logger.warning("[AUTH][SERVICE] Registration failed: account already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        auth_logger.info("[AUTH][SERVICE] Hashing password with bcrypt")
        hashed = hash_password(password)
        new_user = await self.repo.create_user(email=email, hashed_password=hashed)
        
        auth_logger.info(f"[AUTH][SERVICE] Generating JWT token for user {new_user.id}")
        token = create_access_token(data={"sub": str(new_user.id)})

        return new_user, token

    async def login_user(self, email: str, password: str) -> str:
        """
        Authenticate a user and return a JWT access token.
        - Fetches user by email
        - Verifies password
        - Returns JWT token
        """
        auth_logger.info("[AUTH][SERVICE] Auth service activated — processing login")
        user = await self.repo.get_user_by_email(email)
        if not user:
            auth_logger.warning("[AUTH][SERVICE] Login failed: invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(password, user.hashed_password):
            auth_logger.warning("[AUTH][SERVICE] Login failed: invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        auth_logger.info(f"[AUTH][SERVICE] Generating JWT token for user {user.id}")
        return create_access_token(data={"sub": str(user.id)})

    async def get_current_user(self, token: str) -> User:
        """
        Decode a JWT token and return the corresponding user.
        - Decodes JWT
        - Fetches user from repository by ID
        """
        auth_logger.info("[AUTH][SERVICE] Auth service activated — processing get_current_user")
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            auth_logger.warning("[AUTH][SERVICE] Token validation failed: Missing sub field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
            )

        user = await self.repo.get_user_by_id(uuid.UUID(user_id))
        if not user:
            auth_logger.warning("[AUTH][SERVICE] User lookup failed: user id not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user
