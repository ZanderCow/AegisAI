"""Cryptographic utilities for JWTs.

This module provides functions for generating secure
JSON Web Tokens (JWT) for authentication.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("SECURITY")

_bearer_scheme = HTTPBearer()

def create_token(data: dict[str, Any]) -> str:
    """Encodes a payload into a secure JSON Web Token (JWT).
    
    Generates a token signed with the application's secret key, appending
    a standard `exp` (expiration) claim based on the configured token lifespan.
    
    Args:
        data (dict[str, Any]): The payload dictionary (claims) to encode in the token.
        
    Returns:
        str: The fully encoded, signed JWT string.
    """
    logger.info(f"Creating JWT token for user ID: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> str:
    """Extracts and validates the authenticated user's ID from a Bearer token.

    Decodes the JWT from the Authorization header and returns the subject
    claim, which represents the user's ID.

    Args:
        credentials (HTTPAuthorizationCredentials): The HTTP Bearer credentials
            extracted from the Authorization header by FastAPI's security scheme.

    Returns:
        str: The user ID (the 'sub' claim) extracted from the token payload.

    Raises:
        HTTPException: 401 if the token is expired or invalid.
        HTTPException: 401 if the token payload does not contain a 'sub' claim.
    """
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("JWT payload missing 'sub' claim")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return user_id
