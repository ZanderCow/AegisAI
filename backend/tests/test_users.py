"""
test_users.py
=============
Integration tests for user-related API endpoints.

These tests exercise the **signup**, **login**, and **user retrieval**
flows through the FastAPI test client, verifying that the application
correctly creates users, issues JWT tokens, and returns the expected
HTTP status codes.

Each test initialises a fresh Beanie connection to a dedicated test
database (``aegis_ai_test_db``) so that production data is never
touched.

Test Matrix
-----------
==========================================  ========  ==================
Test                                        Method    Expected Status
==========================================  ========  ==================
``test_signup_new_user``                    POST      201 Created
``test_signup_duplicate_email``             POST      400 Bad Request
``test_signup_duplicate_username``          POST      400 Bad Request
``test_login_valid_credentials``            POST      200 OK
``test_login_wrong_password``               POST      400 Bad Request
``test_login_nonexistent_user``             POST      400 Bad Request
``test_get_current_user``                   GET       200 OK
``test_get_current_user_invalid_token``     GET       403 Forbidden
``test_create_and_read_user_via_crud``      n/a       n/a (CRUD only)
==========================================  ========  ==================
"""

import uuid
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.core.db import init_db
from src.core.security import create_access_token, get_password_hash
from src.crud.user import user_crud
from src.models.user_model import User

# ── Test Configuration ──────────────────────────────────────────────────

# Override the database name so tests never touch production data.
settings.DATABASE_NAME = "aegis_ai_test_db"


# ── Helpers ─────────────────────────────────────────────────────────────

def _unique_email(label: str = "user") -> str:
    """Generate a unique email address to avoid test collisions."""
    return f"{label}-{uuid.uuid4().hex[:8]}@test.com"


def _unique_username(label: str = "user") -> str:
    """Generate a unique username to avoid test collisions."""
    return f"{label}_{uuid.uuid4().hex[:8]}"


async def _get_test_client() -> AsyncClient:
    """Build an ``AsyncClient`` wired to the application under test.

    Returns
    -------
    AsyncClient
        An httpx async client configured with the FastAPI ``app``
        instance and a base URL matching the API v1 prefix.
    """
    # Lazy import so the app module reads the overridden settings.
    from src.main import app  # noqa: WPS433

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _create_test_user(
    email: str | None = None,
    username: str | None = None,
    password: str = "StrongP@ss1",
) -> User:
    """Insert a user directly via the ORM for test setup.

    Parameters
    ----------
    email : str | None
        Email for the new user; auto-generated if ``None``.
    username : str | None
        Username for the new user; auto-generated if ``None``.
    password : str
        Plain-text password to hash and store.

    Returns
    -------
    User
        The persisted Beanie ``User`` document.
    """
    user = User(
        email=email or _unique_email("setup"),
        username=username or _unique_username("setup"),
        hashed_password=get_password_hash(password),
    )
    await user.insert()
    return user


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
async def _init_test_db() -> None:
    """Initialise the Beanie ODM before every test.

    This fixture ensures the MongoDB connection and document models are
    ready.  It runs automatically for each test function.
    """
    await init_db()


# ── Tests – Signup ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signup_new_user() -> None:
    """POST /api/v1/auth/signup should create a user and return 201."""
    client = await _get_test_client()
    email = _unique_email("signup")
    username = _unique_username("signup")

    payload = {
        "email": email,
        "username": username,
        "password": "Str0ngP@ssword!",
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/signup",
            json=payload,
        )

    # Verify the user was created successfully.
    assert response.status_code == 201

    body = response.json()

    # Verify every field we sent is echoed back.
    assert body["email"] == email
    assert body["username"] == username
    assert body["is_active"] is True

    # Verify server-generated fields are present.
    assert "id" in body or "_id" in body
    assert "created_at" in body

    # Clean up the created user.
    created_user = await User.find_one(User.email == email)
    if created_user:
        await created_user.delete()


@pytest.mark.asyncio
async def test_signup_duplicate_email() -> None:
    """POST /api/v1/auth/signup with an existing email should return 400."""
    existing = await _create_test_user()

    client = await _get_test_client()
    payload = {
        "email": existing.email,
        "username": _unique_username("dup-email"),
        "password": "An0therP@ss!",
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/signup",
            json=payload,
        )

    # The server should reject the duplicate email.
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

    # Clean up.
    await existing.delete()


@pytest.mark.asyncio
async def test_signup_duplicate_username() -> None:
    """POST /api/v1/auth/signup with an existing username should return 400."""
    existing = await _create_test_user()

    client = await _get_test_client()
    payload = {
        "email": _unique_email("dup-uname"),
        "username": existing.username,
        "password": "An0therP@ss!",
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/signup",
            json=payload,
        )

    # The server should reject the duplicate username.
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()

    # Clean up.
    await existing.delete()


# ── Tests – Login ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_valid_credentials() -> None:
    """POST /api/v1/auth/login/access-token should return 200 with a JWT."""
    password = "V@lidP4ssword!"
    user = await _create_test_user(password=password)

    client = await _get_test_client()

    # OAuth2 token endpoint expects form-encoded data.
    form_data = {
        "username": user.email,
        "password": password,
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data=form_data,
        )

    # Verify the token was issued.
    assert response.status_code == 200

    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    # Clean up.
    await user.delete()


@pytest.mark.asyncio
async def test_login_wrong_password() -> None:
    """POST /api/v1/auth/login/access-token with wrong password should return 400."""
    user = await _create_test_user(password="C0rrectP@ss!")

    client = await _get_test_client()
    form_data = {
        "username": user.email,
        "password": "Wr0ngP@ssword!",
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data=form_data,
        )

    # Wrong password must be rejected.
    assert response.status_code == 400

    # Clean up.
    await user.delete()


@pytest.mark.asyncio
async def test_login_nonexistent_user() -> None:
    """POST /api/v1/auth/login/access-token for unknown user should return 400."""
    client = await _get_test_client()
    form_data = {
        "username": _unique_email("ghost"),
        "password": "D0esN0tM@tter!",
    }

    async with client:
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login/access-token",
            data=form_data,
        )

    # Non-existent user must be rejected.
    assert response.status_code == 400


# ── Tests – Current User ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_current_user() -> None:
    """GET /api/v1/users/me with a valid token should return 200."""
    user = await _create_test_user()

    # Mint a valid JWT for the test user.
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=30),
    )

    client = await _get_test_client()
    headers = {"Authorization": f"Bearer {token}"}

    async with client:
        response = await client.get(
            f"{settings.API_V1_STR}/users/me",
            headers=headers,
        )

    # Verify the current user is returned.
    assert response.status_code == 200

    body = response.json()
    assert body["email"] == user.email
    assert body["username"] == user.username

    # Clean up.
    await user.delete()


@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    """GET /api/v1/users/me with a bad token should return 403."""
    client = await _get_test_client()
    headers = {"Authorization": "Bearer invalid-token-value"}

    async with client:
        response = await client.get(
            f"{settings.API_V1_STR}/users/me",
            headers=headers,
        )

    # Invalid token should be rejected.
    assert response.status_code == 403


# ── Tests – CRUD Layer ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_read_user_via_crud() -> None:
    """CRUDUser.create() should persist a user retrievable by email."""
    from src.schemas.users import UserCreate  # noqa: WPS433

    email = _unique_email("crud")
    username = _unique_username("crud")

    # Create a user through the CRUD layer.
    user_in = UserCreate(
        email=email,
        username=username,
        password="CrudT3stP@ss!",
    )
    created = await user_crud.create(user_in)

    # Verify the created user is retrievable.
    assert created.email == email
    assert created.username == username
    assert created.is_active is True

    # Retrieve by email.
    found = await user_crud.get_by_email(email)
    assert found is not None
    assert found.username == username

    # Retrieve by username.
    found_by_name = await user_crud.get_by_username(username)
    assert found_by_name is not None
    assert found_by_name.email == email

    # Clean up.
    await created.delete()


@pytest.mark.asyncio
async def test_authenticate_user_via_crud() -> None:
    """CRUDUser.authenticate() should return the user for valid credentials."""
    email = _unique_email("auth-crud")
    password = "Auth3nticP@ss!"
    user = await _create_test_user(email=email, password=password)

    # Valid credentials should return the user.
    authed = await user_crud.authenticate(email=email, password=password)
    assert authed is not None
    assert authed.email == email

    # Wrong password should return None.
    bad = await user_crud.authenticate(email=email, password="Wr0ngOne!")
    assert bad is None

    # Non-existent email should return None.
    ghost = await user_crud.authenticate(
        email=_unique_email("ghost"),
        password=password,
    )
    assert ghost is None

    # Clean up.
    await user.delete()
