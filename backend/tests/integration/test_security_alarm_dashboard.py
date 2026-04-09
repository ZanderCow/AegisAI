"""Integration tests for the security alarm dashboard endpoint."""
from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation_model import Conversation
from src.models.flagged_event_model import Alarm
from src.models.user_model import ROLE_SECURITY, User


async def _signup_and_get_headers(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> dict[str, str]:
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
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().one()
    user.role = role
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_conversation(
    db_session: AsyncSession,
    user: User,
    title: str,
) -> Conversation:
    conversation = Conversation(
        title=title,
        user_id=user.id,
        provider="deepseek",
        model="deepseek-chat",
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest.mark.asyncio
async def test_security_alarm_dashboard_returns_alarm_rows_newest_first(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime.now(timezone.utc)

    security_headers = await _signup_and_get_headers(client, "security-alarms@example.com")
    await _set_user_role(db_session, "security-alarms@example.com", ROLE_SECURITY)

    await _signup_and_get_headers(client, "flagged-user@example.com")
    flagged_user = await _set_user_role(db_session, "flagged-user@example.com", "user")
    conversation = await _create_conversation(db_session, flagged_user, "Flagged conversation")

    older_alarm = Alarm(
        id=uuid.uuid4(),
        user_id=flagged_user.id,
        conversation_id=conversation.id,
        message_content="older harmful request",
        filter_type="keyword",
        provider="deepseek",
        created_at=now - timedelta(minutes=10),
    )
    newer_alarm = Alarm(
        id=uuid.uuid4(),
        user_id=flagged_user.id,
        conversation_id=conversation.id,
        message_content="newer harmful request",
        filter_type="provider",
        provider="deepseek",
        created_at=now - timedelta(minutes=1),
    )
    db_session.add_all([older_alarm, newer_alarm])
    await db_session.commit()

    response = await client.get(
        "/api/v1/chat/security/alarms",
        headers=security_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["message_content"] for item in data] == [
        "newer harmful request",
        "older harmful request",
    ]
    assert data[0]["user_email"] == "flagged-user@example.com"
    assert data[0]["filter_type"] == "provider"
    assert data[1]["filter_type"] == "keyword"


@pytest.mark.asyncio
async def test_security_alarm_dashboard_forbids_standard_users(
    client: AsyncClient,
) -> None:
    user_headers = await _signup_and_get_headers(client, "standard-alarms@example.com")

    response = await client.get(
        "/api/v1/chat/security/alarms",
        headers=user_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Security role required"
