"""Unit tests for the JWT security module.

This module contains unit tests verifying the behavior of encoding JSON Web Tokens
inside the `src.security.jwt` module.
"""
from typing import Any
import pytest
import jwt
from datetime import datetime, timezone

from src.security.jwt import create_token
from src.core.config import settings

def test_create_token_success() -> None:
    """Tests successful creation of a JWT.
    
    Verifies that the `create_token` function correctly encodes data into a valid 
    JWT string, and that the payload successfully decodes using the application's 
    secret key and algorithm.
    """
    data = {"sub": "user_12345"}
    token = create_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Verify we can decode it with the application settings
    decoded_payload = jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    assert decoded_payload["sub"] == "user_12345"
    assert "exp" in decoded_payload
    
    # Verify that the expiration time was set in the future
    exp_timestamp = decoded_payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    assert exp_datetime > datetime.now(timezone.utc)

def test_create_token_custom_expiry() -> None:
    """Tests that expires_minutes overrides the default expiration window."""
    token = create_token({"sub": "user_custom_exp"}, expires_minutes=5)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    # Should expire in roughly 5 minutes, not the default 30
    delta_minutes = (exp - now).total_seconds() / 60
    assert 4 <= delta_minutes <= 6


def test_create_token_does_not_mutate_input() -> None:
    """Tests that the input dictionary is not mutated.
    
    Verifies that the `create_token` function copies the input data payload
    rather than mutating the original dictionary by injecting the `exp` key.
    """
    data: dict[str, Any] = {"sub": "user_12345"}
    original_data = data.copy()
    
    create_token(data)
    
    # The original data should not have an 'exp' key added to it
    assert data == original_data
    assert "exp" not in data
