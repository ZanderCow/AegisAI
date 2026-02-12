"""
test_users.py
=============
Development integration tests for the **Users** API.

These tests hit a **real PostgreSQL** database (configured via the
``DATABASE_URL`` environment variable).  They create fake data to exercise
every endpoint and are **not** suitable for production pipelines.

Test Matrix
-----------
=================================  ========  ==================
Test                               Method    Expected Status
=================================  ========  ==================
``test_create_user``               POST      201 Created
``test_create_user_duplicate``     POST      500 (unique violation)
``test_list_users``                GET       200 OK
``test_get_user_by_id``            GET       200 OK
``test_get_user_not_found``        GET       404 Not Found
=================================  ========  ==================
"""

import uuid

from httpx import AsyncClient


# ── Helpers ─────────────────────────────────────────────────────────────────

def _unique_email(label: str = "user") -> str:
    """Generate a unique email address to avoid test collisions."""
    return f"{label}_{uuid.uuid4().hex[:8]}@test.example.com"


def _unique_username(label: str = "user") -> str:
    """Generate a unique username to avoid test collisions."""
    return f"{label}_{uuid.uuid4().hex[:8]}"


# ── Tests ───────────────────────────────────────────────────────────────────


async def test_create_user(client: AsyncClient) -> None:
    """POST /users/ should create a user and return 201 with all fields."""
    payload = {
        "email": _unique_email("create"),
        "username": _unique_username("create"),
        "full_name": "Test Create User",
    }

    response = await client.post("/users/", json=payload)

    assert response.status_code == 201, response.text
    body = response.json()

    # Verify every field we sent is echoed back.
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["full_name"] == payload["full_name"]

    # Verify server-generated fields are present.
    assert "id" in body
    assert "is_active" in body
    assert body["is_active"] is True
    assert "created_at" in body
    assert "updated_at" in body


async def test_create_user_without_full_name(client: AsyncClient) -> None:
    """POST /users/ with no full_name should succeed – the field is optional."""
    payload = {
        "email": _unique_email("nofull"),
        "username": _unique_username("nofull"),
    }

    response = await client.post("/users/", json=payload)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["full_name"] is None


async def test_list_users(client: AsyncClient) -> None:
    """GET /users/ should return a list that includes newly created users."""
    # Create two users so the list is non-empty.
    user_a = {
        "email": _unique_email("list_a"),
        "username": _unique_username("list_a"),
        "full_name": "List User A",
    }
    user_b = {
        "email": _unique_email("list_b"),
        "username": _unique_username("list_b"),
        "full_name": "List User B",
    }

    resp_a = await client.post("/users/", json=user_a)
    resp_b = await client.post("/users/", json=user_b)
    assert resp_a.status_code == 201
    assert resp_b.status_code == 201

    # Fetch the list.
    response = await client.get("/users/")

    assert response.status_code == 200, response.text
    body = response.json()

    # body should be a list containing at least the two users we just made.
    assert isinstance(body, list)
    returned_emails = {u["email"] for u in body}
    assert user_a["email"] in returned_emails
    assert user_b["email"] in returned_emails


async def test_get_user_by_id(client: AsyncClient) -> None:
    """GET /users/{id} should return the correct user."""
    payload = {
        "email": _unique_email("getid"),
        "username": _unique_username("getid"),
        "full_name": "Get By ID User",
    }
    create_resp = await client.post("/users/", json=payload)
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    user_id = created_user["id"]

    # Retrieve by ID.
    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == user_id
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["full_name"] == payload["full_name"]


async def test_get_user_not_found(client: AsyncClient) -> None:
    """GET /users/{id} with a non-existent UUID should return 404."""
    fake_id = str(uuid.uuid4())

    response = await client.get(f"/users/{fake_id}")

    assert response.status_code == 404, response.text
    body = response.json()
    assert "not found" in body["detail"].lower()
