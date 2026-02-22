"""
Unit Tests — User Schemas (schemas/user_schema.py)
Tests: UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
Run with: pytest tests/unit/test_user_schema.py -v
"""
import pytest
from pydantic import ValidationError

from src.schemas.user_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)


# ---------------------------------------------------------------------------
# UserRegisterRequest
# ---------------------------------------------------------------------------

class TestUserRegisterRequest:
    def test_valid_input(self):
        schema = UserRegisterRequest(email="user@example.com", password="securepass")
        assert schema.email == "user@example.com"
        assert schema.password == "securepass"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(email="not-an-email", password="securepass")

    def test_password_too_short_raises(self):
        """Password must be at least 8 characters."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(email="user@example.com", password="short")

    def test_password_exactly_8_chars_is_valid(self):
        schema = UserRegisterRequest(email="user@example.com", password="exactly8")
        assert schema.password == "exactly8"

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(password="securepass")

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(email="user@example.com")

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(email="", password="securepass")


# ---------------------------------------------------------------------------
# UserLoginRequest
# ---------------------------------------------------------------------------

class TestUserLoginRequest:
    def test_valid_input(self):
        schema = UserLoginRequest(email="user@example.com", password="anypassword")
        assert schema.email == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserLoginRequest(email="bad-email", password="anypassword")

    def test_missing_fields_raise(self):
        with pytest.raises(ValidationError):
            UserLoginRequest(email="user@example.com")

    def test_empty_password_is_allowed(self):
        """Login schema has no min_length — the service handles auth failure."""
        schema = UserLoginRequest(email="user@example.com", password="")
        assert schema.password == ""


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------

class TestUserResponse:
    def test_valid_construction(self):
        schema = UserResponse(id=1, email="user@example.com")
        assert schema.id == 1
        assert schema.email == "user@example.com"

    def test_no_hashed_password_field(self):
        """UserResponse must never expose hashed_password."""
        assert not hasattr(UserResponse, "hashed_password")

    def test_from_orm_model(self):
        """Schema should construct from an ORM-like object (from_attributes=True)."""
        class FakeUser:
            id = 5
            email = "orm@example.com"

        schema = UserResponse.model_validate(FakeUser())
        assert schema.id == 5
        assert schema.email == "orm@example.com"

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            UserResponse(email="user@example.com")

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            UserResponse(id=1)


# ---------------------------------------------------------------------------
# TokenResponse
# ---------------------------------------------------------------------------

class TestTokenResponse:
    def test_valid_token_response(self):
        schema = TokenResponse(access_token="some.jwt.token")
        assert schema.access_token == "some.jwt.token"
        assert schema.token_type == "bearer"  # default value

    def test_token_type_default_is_bearer(self):
        schema = TokenResponse(access_token="abc")
        assert schema.token_type == "bearer"

    def test_token_type_can_be_overridden(self):
        schema = TokenResponse(access_token="abc", token_type="custom")
        assert schema.token_type == "custom"

    def test_missing_access_token_raises(self):
        with pytest.raises(ValidationError):
            TokenResponse()