"""
Integration tests for /api/v1/auth endpoints.

These tests hit the real FastAPI app (via ASGI transport) against a real
PostgreSQL database, exercising every layer: endpoint → service → repo → DB.
"""
import pytest


SIGNUP_URL = "/api/v1/auth/signup"
LOGIN_URL = "/api/v1/auth/login/access-token"

VALID_EMAIL = "testuser@example.com"
VALID_PASSWORD = "StrongPass1!"


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class TestSignup:
    async def test_signup_returns_201_with_token(self, client):
        resp = await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == VALID_EMAIL
        assert "user_id" in body
        assert "jwt" in body
        assert "created_at" in body
        assert len(body["jwt"]) > 20


    async def test_signup_duplicate_email_returns_400(self, client):
        payload = {"email": VALID_EMAIL, "password": VALID_PASSWORD}
        await client.post(SIGNUP_URL, json=payload)
        resp = await client.post(SIGNUP_URL, json=payload)
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]


    async def test_signup_invalid_email_returns_422(self, client):
        resp = await client.post(SIGNUP_URL, json={"email": "not-an-email", "password": VALID_PASSWORD})
        assert resp.status_code == 422


    async def test_signup_short_password_returns_422(self, client):
        resp = await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": "short"})
        assert resp.status_code == 422


    async def test_signup_missing_fields_returns_422(self, client):
        resp = await client.post(SIGNUP_URL, json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    async def test_login_returns_200_with_access_token(self, client):
        # Register first
        await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})

        resp = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20


    async def test_login_wrong_password_returns_401(self, client):
        await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})

        resp = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": "WrongPass99!"})
        assert resp.status_code == 401


    async def test_login_unknown_email_returns_401(self, client):
        resp = await client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": VALID_PASSWORD})
        assert resp.status_code == 401


    async def test_login_invalid_email_returns_422(self, client):
        resp = await client.post(LOGIN_URL, json={"email": "bad-email", "password": VALID_PASSWORD})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Signup token is a valid JWT (round-trip)
# ---------------------------------------------------------------------------

class TestJWT:
    async def test_signup_jwt_is_decodable(self, client):
        """The JWT returned by signup must be a well-formed three-part token."""
        resp = await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert resp.status_code == 201
        jwt = resp.json()["jwt"]
        parts = jwt.split(".")
        assert len(parts) == 3, "JWT must have header.payload.signature format"


    async def test_login_token_differs_from_signup_token(self, client):
        """Each call issues a fresh token (different iat/exp timestamps)."""
        import asyncio

        resp1 = await client.post(SIGNUP_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        await asyncio.sleep(1)  # ensure exp differs
        resp2 = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})

        signup_token = resp1.json()["jwt"]
        login_token = resp2.json()["access_token"]
        assert signup_token != login_token
