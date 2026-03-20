import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_successful_signup(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "newuser@example.com", "password": "supersecurepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_duplicate_email_signup(client: AsyncClient):
    payload = {"email": "duplicate@example.com", "password": "password123"}
    # First sign up
    await client.post("/api/v1/auth/signup", json=payload)
    # Attempt duplicate
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient):
    payload = {"email": "login@example.com", "password": "password123"}
    await client.post("/api/v1/auth/signup", json=payload)

    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_wrong_password_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "wrongpwd@example.com", "password": "password123"}
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpwd@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_unknown_email_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
