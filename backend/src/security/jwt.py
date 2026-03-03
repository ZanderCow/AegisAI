"""Cryptographic utilities for JWTs.

This module provides functions for generating secure
JSON Web Tokens (JWT) for authentication.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("SECURITY")

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
