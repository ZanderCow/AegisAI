"""
Unit Tests — JWT Security Layer (security/jwt.py)
Tests: create_access_token, decode_access_token
Run with: pytest tests/unit/test_jwt.py -v
"""
import pytest
from unittest.mock import patch
from datetime import timedelta
from fastapi import HTTPException

from src.security.jwt import create_access_token, decode_access_token


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_a_string(self):
        """Token output should be a non-empty string."""
        token = create_access_token(data={"sub": "1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_parts(self):
        """JWT format is header.payload.signature."""
        token = create_access_token(data={"sub": "1"})
        assert token.count(".") == 2

    def test_different_payloads_produce_different_tokens(self):
        token_a = create_access_token(data={"sub": "1"})
        token_b = create_access_token(data={"sub": "2"})
        assert token_a != token_b

    def test_custom_expiry_accepted(self):
        """Should not raise when a custom expiry delta is passed."""
        token = create_access_token(data={"sub": "1"}, expires_delta=timedelta(minutes=60))
        assert token is not None


# ---------------------------------------------------------------------------
# decode_access_token
# ---------------------------------------------------------------------------

class TestDecodeAccessToken:
    def test_decode_valid_token(self):
        """A token we just created should decode back cleanly."""
        token = create_access_token(data={"sub": "42"})
        payload = decode_access_token(token)
        assert payload["sub"] == "42"

    def test_decode_preserves_extra_claims(self):
        """Any extra claims embedded at creation should survive decoding."""
        token = create_access_token(data={"sub": "1", "role": "admin"})
        payload = decode_access_token(token)
        assert payload.get("role") == "admin"

    def test_decode_expired_token_raises_401(self):
        """An already-expired token should raise HTTP 401."""
        token = create_access_token(data={"sub": "1"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc:
            decode_access_token(token)
        assert exc.value.status_code == 401

    def test_decode_tampered_token_raises_401(self):
        """A token with a modified payload should be rejected."""
        token = create_access_token(data={"sub": "1"})
        tampered = token[:-5] + "XXXXX"  # corrupt the signature
        with pytest.raises(HTTPException) as exc:
            decode_access_token(tampered)
        assert exc.value.status_code == 401

    def test_decode_garbage_string_raises_401(self):
        """A completely invalid string should raise HTTP 401."""
        with pytest.raises(HTTPException) as exc:
            decode_access_token("not.a.token")
        assert exc.value.status_code == 401

    def test_decode_empty_string_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_access_token("")
        assert exc.value.status_code == 401