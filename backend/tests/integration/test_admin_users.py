"""Integration tests for admin user-management endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation_model import Conversation, Message
from src.models.document_model import Document
from src.models.flagged_event_model import Alarm
from src.models.user_model import ROLE_ADMIN, User


async def _signup(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> None:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201


async def _login_headers(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _set_user_fields(
    db_session: AsyncSession,
    email: str,
    *,
    role: str | None = None,
    full_name: str | None = None,
) -> User:
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().one()
    if role is not None:
        user.role = role
    if full_name is not None:
        user.full_name = full_name
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_admin_users_list_returns_live_user_fields(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _signup(client, "admin-users@example.com")
    await _set_user_fields(
        db_session,
        "admin-users@example.com",
        role=ROLE_ADMIN,
        full_name="Alex Admin",
    )
    admin_headers = await _login_headers(client, "admin-users@example.com")

    await _signup(client, "member-users@example.com")
    await _set_user_fields(
        db_session,
        "member-users@example.com",
        full_name="Casey Member",
    )
    await _login_headers(client, "member-users@example.com")

    response = await client.get("/api/v1/admin/users", headers=admin_headers)

    assert response.status_code == 200
    users = {item["email"]: item for item in response.json()}

    assert users["admin-users@example.com"]["full_name"] == "Alex Admin"
    assert users["admin-users@example.com"]["role"] == ROLE_ADMIN
    assert users["admin-users@example.com"]["created_at"]
    assert users["admin-users@example.com"]["last_login"] is not None

    assert users["member-users@example.com"]["full_name"] == "Casey Member"
    assert users["member-users@example.com"]["role"] == "user"
    assert users["member-users@example.com"]["created_at"]
    assert users["member-users@example.com"]["last_login"] is not None


@pytest.mark.asyncio
async def test_admin_users_delete_hard_deletes_target_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _signup(client, "delete-admin@example.com")
    await _set_user_fields(db_session, "delete-admin@example.com", role=ROLE_ADMIN)
    admin_headers = await _login_headers(client, "delete-admin@example.com")

    await _signup(client, "delete-target@example.com")
    target_user = await _set_user_fields(
        db_session,
        "delete-target@example.com",
        full_name="Delete Me",
    )
    conversation = Conversation(
        title="Delete Cascade Conversation",
        user_id=target_user.id,
        provider="groq",
        model="llama-3.1-8b-instant",
    )
    db_session.add(conversation)
    await db_session.flush()
    db_session.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content="delete me too",
        )
    )
    db_session.add(
        Alarm(
            user_id=target_user.id,
            conversation_id=conversation.id,
            message_content="delete cascade alarm",
            filter_type="keyword",
            provider="groq",
        )
    )
    db_session.add(
        Document(
            title="Delete Cascade Document",
            description="owned by the deleted user",
            filename="cascade.pdf",
            file_size=1024,
            status="active",
            uploaded_by=target_user.id,
            allowed_roles=["user"],
            chroma_doc_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/admin/users/{target_user.id}",
        headers=admin_headers,
    )

    assert response.status_code == 204

    remaining = await db_session.execute(
        select(User).where(User.email == "delete-target@example.com")
    )
    assert remaining.scalars().first() is None
    remaining_conversations = await db_session.execute(
        select(Conversation).where(Conversation.user_id == target_user.id)
    )
    remaining_documents = await db_session.execute(
        select(Document).where(Document.uploaded_by == target_user.id)
    )
    remaining_alarms = await db_session.execute(
        select(Alarm).where(Alarm.user_id == target_user.id)
    )
    assert remaining_conversations.scalars().first() is None
    assert remaining_documents.scalars().first() is None
    assert remaining_alarms.scalars().first() is None


@pytest.mark.asyncio
async def test_admin_users_patch_updates_role(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _signup(client, "role-admin@example.com")
    await _set_user_fields(db_session, "role-admin@example.com", role=ROLE_ADMIN)
    admin_headers = await _login_headers(client, "role-admin@example.com")

    await _signup(client, "role-target@example.com")
    target_user = await _set_user_fields(
        db_session,
        "role-target@example.com",
        full_name="Role Target",
    )

    response = await client.patch(
        f"/api/v1/admin/users/{target_user.id}/role",
        headers=admin_headers,
        json={"role": "security"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(target_user.id)
    assert data["email"] == "role-target@example.com"
    assert data["full_name"] == "Role Target"
    assert data["role"] == "security"

    await db_session.refresh(target_user)
    assert target_user.role == "security"


@pytest.mark.asyncio
async def test_admin_users_endpoints_forbid_non_admin_requesters(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _signup(client, "standard-requester@example.com")
    requester_headers = await _login_headers(client, "standard-requester@example.com")

    await _signup(client, "standard-target@example.com")
    target_user = await _set_user_fields(
        db_session,
        "standard-target@example.com",
        full_name="Standard Target",
    )

    list_response = await client.get("/api/v1/admin/users", headers=requester_headers)
    delete_response = await client.delete(
        f"/api/v1/admin/users/{target_user.id}",
        headers=requester_headers,
    )
    patch_response = await client.patch(
        f"/api/v1/admin/users/{target_user.id}/role",
        headers=requester_headers,
        json={"role": "admin"},
    )

    assert list_response.status_code == 403
    assert list_response.json()["detail"] == "Admin role required"
    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "Admin role required"
    assert patch_response.status_code == 403
    assert patch_response.json()["detail"] == "Admin role required"
