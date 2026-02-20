"""
JWT Security Layer (security/jwt.py)
Handles creation and decoding of JWT access tokens.
Depends on: python-jose, core/config.py (for SECRET_KEY and ALGORITHM settings)
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status

from core.config import settings


# ---------------------------------------------------------------------------
# Create Token
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generate a signed JWT access token.

    - data: payload to encode (must include "sub" with the user ID as a string)
    - expires_delta: optional custom expiry; defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES
    """
    payload = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload.update({"exp": expire})

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# ---------------------------------------------------------------------------
# Decode Token
# ---------------------------------------------------------------------------

def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    - Returns the payload dict if the token is valid and not expired.
    - Raises HTTP 401 for any invalid, expired, or malformed token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )