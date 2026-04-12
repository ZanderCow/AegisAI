"""Integration tests for the authentication API endpoints.

These tests exercise the signup and login flows through the public HTTP API,
verifying successful token issuance as well as common failure cases such as
duplicate registrations and invalid credentials.
"""

import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from src.security.jwt import create_token, decode_token


@pytest.mark.asyncio
async def test_successful_signup(client: AsyncClient) -> None:
    """Verify signup returns a bearer token for a new account.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "newuser@example.com", "password": "supersecurepassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    payload = decode_token(data["access_token"])
    assert payload["email"] == "newuser@example.com"
    assert payload["role"] == "user"


@pytest.mark.asyncio
async def test_successful_signup_accepts_explicit_user_role(client: AsyncClient) -> None:
    """Verify explicit user-role signup is accepted and encoded in the JWT."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "explicituser@example.com", "password": "supersecurepassword", "role": "user"},
    )

    assert response.status_code == 201
    data = response.json()
    payload = decode_token(data["access_token"])
    assert payload["email"] == "explicituser@example.com"
    assert payload["role"] == "user"


@pytest.mark.asyncio
async def test_duplicate_email_signup(client: AsyncClient) -> None:
    """Verify a second signup with the same email is rejected.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    payload = {"email": "duplicate@example.com", "password": "password123"}
    await client.post("/api/v1/auth/signup", json=payload)
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient) -> None:
    """Verify login returns a bearer token for a registered user.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    payload = {"email": "login@example.com", "password": "password123"}
    await client.post("/api/v1/auth/signup", json=payload)

    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_wrong_password_login(client: AsyncClient) -> None:
    """Verify login fails when the password does not match the stored hash.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "wrongpwd@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpwd@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_unknown_email_login(client: AsyncClient) -> None:
    """Verify login fails when the email address is not registered.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ---------------------------------------------------------------------------
# MFA-enabled login tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_mfa_enabled_returns_duo_redirect(client: AsyncClient) -> None:
    """Verify login returns a Duo auth URL and state token when MFA is enabled."""
    payload = {"email": "mfauser@example.com", "password": "password123"}
    await client.post("/api/v1/auth/signup", json=payload)

    mock_duo = MagicMock()
    mock_duo.generate_state.return_value = "test_duo_state"
    mock_duo.create_auth_url.return_value = "https://api-test.duosecurity.com/oauth/v1/authorize?test=1"

    with patch("src.service.auth_service.settings.MFA_ENABLED", True), \
         patch("src.service.auth_service.get_duo_client", return_value=mock_duo):
        response = await client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["mfa_required"] is True
    assert "duo_auth_url" in data
    assert "state_token" in data
    mock_duo.create_auth_url.assert_called_once_with(payload["email"], "test_duo_state")


@pytest.mark.asyncio
async def test_login_mfa_enabled_wrong_password(client: AsyncClient) -> None:
    """Verify login still rejects bad credentials even when MFA is enabled."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "mfabadpwd@example.com", "password": "correctpassword"},
    )

    with patch("src.service.auth_service.settings.MFA_ENABLED", True):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "mfabadpwd@example.com", "password": "wrongpassword"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ---------------------------------------------------------------------------
# Duo callback tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duo_callback_success(client: AsyncClient) -> None:
    """Verify a valid Duo callback exchanges the code for a session JWT."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "duocallback@example.com", "password": "password123"},
    )

    state = "valid_duo_state"
    state_token = create_token(
        {"sub": "some-user-id", "email": "duocallback@example.com", "duo_state": state, "type": "mfa_pending"},
        expires_minutes=5,
    )

    mock_duo = MagicMock()
    mock_duo.exchange_authorization_code_for_2fa_result.return_value = {"preferred_username": "duocallback@example.com"}

    with patch("src.service.auth_service.get_duo_client", return_value=mock_duo):
        response = await client.post(
            "/api/v1/auth/duo/callback",
            json={"duo_code": "test_duo_code", "state": state, "state_token": state_token},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duo_callback_state_mismatch(client: AsyncClient) -> None:
    """Verify the callback is rejected when the state does not match the token."""
    state_token = create_token(
        {"sub": "some-user-id", "email": "mismatch@example.com", "duo_state": "expected_state", "type": "mfa_pending"},
        expires_minutes=5,
    )

    response = await client.post(
        "/api/v1/auth/duo/callback",
        json={"duo_code": "some_code", "state": "tampered_state", "state_token": state_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "State mismatch"


@pytest.mark.asyncio
async def test_duo_callback_invalid_state_token(client: AsyncClient) -> None:
    """Verify the callback is rejected when the state token is malformed."""
    response = await client.post(
        "/api/v1/auth/duo/callback",
        json={"duo_code": "some_code", "state": "some_state", "state_token": "not.a.valid.jwt"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid state token"


@pytest.mark.asyncio
async def test_duo_callback_duo_verification_fails(client: AsyncClient) -> None:
    """Verify the callback is rejected when Duo rejects the authorization code."""
    from duo_universal.client import DuoException

    state = "valid_state"
    state_token = create_token(
        {"sub": "some-user-id", "email": "duofail@example.com", "duo_state": state, "type": "mfa_pending"},
        expires_minutes=5,
    )

    mock_duo = MagicMock()
    mock_duo.exchange_authorization_code_for_2fa_result.side_effect = DuoException("bad code")

    with patch("src.service.auth_service.get_duo_client", return_value=mock_duo):
        response = await client.post(
            "/api/v1/auth/duo/callback",
            json={"duo_code": "bad_code", "state": state, "state_token": state_token},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "MFA verification failed"
