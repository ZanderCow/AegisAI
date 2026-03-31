"""Integration tests for the authentication API endpoints.

These tests exercise the signup and login flows through the public HTTP API,
verifying successful token issuance as well as common failure cases such as
duplicate registrations and invalid credentials.
"""

import pytest
from httpx import AsyncClient


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
