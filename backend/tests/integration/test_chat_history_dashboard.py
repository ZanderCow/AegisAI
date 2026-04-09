"""Integration tests for the security historic chat dashboard endpoint."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation_model import Conversation, Message
from src.models.user_model import ROLE_ADMIN, ROLE_SECURITY, User


async def _signup_and_get_headers(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> dict[str, str]:
    """Create a user account and return bearer authorization headers."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _set_user_role(
    db_session: AsyncSession,
    email: str,
    role: str,
) -> User:
    """Update a persisted user's role for authorization tests."""
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().one()
    user.role = role
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_conversation_with_messages(
    db_session: AsyncSession,
    user: User,
    title: str,
    created_at: datetime,
    messages: list[tuple[str, str, datetime]],
) -> Conversation:
    """Persist a conversation and its ordered message history directly in the DB."""
    conversation = Conversation(
        title=title,
        user_id=user.id,
        provider="groq",
        model="llama-3.1-8b-instant",
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(conversation)
    await db_session.flush()

    for role, content, message_time in messages:
        db_session.add(
            Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                created_at=message_time,
            )
        )

    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest.mark.asyncio
async def test_security_dashboard_returns_paginated_histories_in_recent_order(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Security users should receive paginated histories ordered by recent activity."""
    now = datetime.now(timezone.utc)

    security_headers = await _signup_and_get_headers(client, "security-history@example.com")
    await _set_user_role(db_session, "security-history@example.com", ROLE_SECURITY)

    await _signup_and_get_headers(client, "employee-one@example.com")
    user_one = await _set_user_role(db_session, "employee-one@example.com", "user")

    await _signup_and_get_headers(client, "employee-two@example.com")
    user_two = await _set_user_role(db_session, "employee-two@example.com", "user")

    older_conversation = await _create_conversation_with_messages(
        db_session,
        user_one,
        title="Older Payroll Review",
        created_at=now - timedelta(days=3),
        messages=[
            ("user", "Can you summarize payroll policy?", now - timedelta(days=2, hours=2)),
            ("assistant", "Here is the payroll summary.", now - timedelta(days=2, hours=1)),
        ],
    )
    newer_conversation = await _create_conversation_with_messages(
        db_session,
        user_two,
        title="Recent Incident Triage",
        created_at=now - timedelta(hours=2),
        messages=[
            ("user", "List yesterday's incidents.", now - timedelta(hours=1)),
            ("assistant", "I found three incidents.", now - timedelta(minutes=30)),
        ],
    )
    newest_empty_conversation = await _create_conversation_with_messages(
        db_session,
        user_one,
        title="Fresh Empty Draft",
        created_at=now - timedelta(minutes=10),
        messages=[],
    )

    first_page = await client.get(
        "/api/v1/chat/security/histories?limit=2&offset=0",
        headers=security_headers,
    )

    assert first_page.status_code == 200
    first_page_data = first_page.json()

    assert first_page_data["total"] == 3
    assert first_page_data["limit"] == 2
    assert first_page_data["offset"] == 0
    assert first_page_data["summary"] == {
        "total_histories": 3,
        "total_messages": 4,
        "recent_activity": 2,
        "unique_users": 2,
    }
    assert [item["title"] for item in first_page_data["items"]] == [
        newest_empty_conversation.title,
        newer_conversation.title,
    ]

    newest_item = first_page_data["items"][0]
    assert newest_item["conversation_id"] == str(newest_empty_conversation.id)
    assert newest_item["message_count"] == 0
    assert newest_item["messages"] == []

    recent_item = first_page_data["items"][1]
    assert recent_item["conversation_id"] == str(newer_conversation.id)
    assert recent_item["user_email"] == "employee-two@example.com"
    assert recent_item["message_count"] == 2
    assert [message["content"] for message in recent_item["messages"]] == [
        "List yesterday's incidents.",
        "I found three incidents.",
    ]

    second_page = await client.get(
        "/api/v1/chat/security/histories?limit=2&offset=2",
        headers=security_headers,
    )

    assert second_page.status_code == 200
    second_page_data = second_page.json()
    assert [item["title"] for item in second_page_data["items"]] == [older_conversation.title]
    assert second_page_data["items"][0]["user_email"] == "employee-one@example.com"


@pytest.mark.asyncio
async def test_security_dashboard_forbids_standard_users(
    client: AsyncClient,
) -> None:
    """Standard users should receive a 403 from the historic chat dashboard."""
    user_headers = await _signup_and_get_headers(client, "standard-history@example.com")

    response = await client.get(
        "/api/v1/chat/security/histories",
        headers=user_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Security role required"


@pytest.mark.asyncio
async def test_security_dashboard_forbids_admin_users(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Admins should not be able to call the security-only historic chat endpoint."""
    admin_headers = await _signup_and_get_headers(client, "admin-history@example.com")
    await _set_user_role(db_session, "admin-history@example.com", ROLE_ADMIN)

    response = await client.get(
        "/api/v1/chat/security/histories",
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Security role required"
