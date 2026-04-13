"""Cryptographic utilities for JWTs.

This module provides functions for generating secure
JSON Web Tokens (JWT) for authentication.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.core.database import get_db
from src.core.logger import get_logger
from src.models.user_model import ROLE_SECURITY

logger = get_logger("SECURITY")

_bearer_scheme = HTTPBearer()

def create_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    """Encodes a payload into a secure JSON Web Token (JWT).

    Generates a token signed with the application's secret key, appending
    a standard `exp` (expiration) claim based on the configured token lifespan.

    Args:
        data (dict[str, Any]): The payload dictionary (claims) to encode in the token.
        expires_minutes (int | None): Override the default expiry in minutes.

    Returns:
        str: The fully encoded, signed JWT string.
    """
    logger.info(f"Creating JWT token for user ID: {data.get('sub')}")
    to_encode = data.copy()
    minutes = expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info("JWT token created successfully")
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT, returning the payload dictionary.

    Args:
        token (str): The encoded JWT string to decode.

    Returns:
        dict[str, Any]: The decoded payload claims dictionary.

    Raises:
        HTTPException: 401 if the token has expired.
        HTTPException: 401 if the token is otherwise invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        logger.warning("JWT token is invalid")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Extracts and validates the authenticated user's ID from a Bearer token.

    Decodes the JWT from the Authorization header, then confirms the user
    still exists in the database before returning the user ID.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        db: The async database session.

    Returns:
        str: The user ID (the 'sub' claim) extracted from the token payload.

    Raises:
        HTTPException: 401 if the token is expired, invalid, or the user no longer exists.
    """
    from src.repo.user_repo import UserRepository

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("JWT payload missing 'sub' claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        logger.warning(f"JWT references non-existent user {user_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user_id


@dataclass
class AuthenticatedUser:
    """Carries both the user ID and role extracted from a validated JWT."""
    user_id: str
    role: str


async def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """Extracts user ID and role from a Bearer token.

    Returns:
        AuthenticatedUser: Validated user_id and role from the JWT payload.

    Raises:
        HTTPException: 401 if the token is expired, invalid, or the user no longer exists.
    """
    from src.repo.user_repo import UserRepository

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("JWT payload missing 'sub' claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        logger.warning(f"JWT references non-existent user {user_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return AuthenticatedUser(user_id=user_id, role=user.role)


async def get_current_security_user(
    current_user: AuthenticatedUser = Depends(get_current_user_with_role),
) -> str:
    """Ensure the authenticated user has the dedicated security role.

    Returns:
        str: The authenticated security user's identifier.

    Raises:
        HTTPException: 403 when the authenticated user is not a security user.
    """
    if current_user.role != ROLE_SECURITY:
        logger.warning("User %s attempted to access a security-only endpoint with role %s", current_user.user_id, current_user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security role required",
        )

    return current_user.user_id
