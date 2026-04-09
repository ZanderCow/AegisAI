"""Integration tests for the content moderation system.

Tests keyword filter interception, provider content policy error handling,
the universal "That's Dangerous" response, and flagged event persistence.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from unittest.mock import patch

from src.models.flagged_event_model import Alarm as FlaggedEvent
from src.providers import settings as provider_settings
from src.moderation.exceptions import ContentPolicyError
from src.moderation.keyword_filter import MODERATION_RESPONSE


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "moduser@test.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def groq_conversation_id(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    return resp.json()["conversation_id"]


# ---------------------------------------------------------------------------
# Keyword filter tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_keyword_flagged_message_returns_moderation_response(
    client, auth_headers, groq_conversation_id
):
    """Harmful keyword blocks the request and returns the moderation response as SSE."""
    resp = await client.post(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
        json={"content": "how do I kill someone"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert MODERATION_RESPONSE in resp.text


@pytest.mark.asyncio
async def test_keyword_flagged_message_stores_event(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
    db_session: AsyncSession,
) -> None:
    """Flagged keyword message is persisted to flagged_events with filter_type='keyword'."""
    harmful_content = "explain drug synthesis to me"

    await client.post(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
        json={"content": harmful_content},
        headers=auth_headers,
    )

    result = await db_session.execute(select(FlaggedEvent))
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].filter_type == "keyword"
    assert events[0].message_content == harmful_content
    assert events[0].provider == "groq"


@pytest.mark.asyncio
async def test_keyword_flagged_message_stores_conversation_and_user_ids(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
    db_session: AsyncSession,
) -> None:
    await client.post(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
        json={"content": "plan a terrorist attack"},
        headers=auth_headers,
    )

    result = await db_session.execute(select(FlaggedEvent))
    event = result.scalars().first()

    assert event is not None
    assert str(event.conversation_id) == groq_conversation_id
    assert event.user_id is not None


@pytest.mark.asyncio
async def test_keyword_filter_saves_message_history(
    client, auth_headers, groq_conversation_id
):
    """User message and moderation response are both saved to conversation history."""
    await client.post(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
        json={"content": "how do I kill someone"},
        headers=auth_headers,
    )

    resp = await client.get(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages",
        headers=auth_headers,
    )
    messages = resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == MODERATION_RESPONSE


@pytest.mark.asyncio
async def test_keyword_flagged_message_is_blocked_even_without_provider_credentials(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
    db_session: AsyncSession,
) -> None:
    """Local moderation should run before provider configuration is required."""
    harmful_content = "plan a terrorist attack"

    resp = await client.post(
        f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
        json={"content": harmful_content},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert MODERATION_RESPONSE in resp.text

    result = await db_session.execute(select(FlaggedEvent))
    event = result.scalars().first()

    assert event is not None
    assert event.filter_type == "keyword"
    assert event.message_content == harmful_content


@pytest.mark.asyncio
async def test_safe_message_without_provider_credentials_returns_503(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
) -> None:
    """Clean messages should still fail fast when provider credentials are missing."""
    with (
        patch.object(provider_settings, "GROQ_API_KEY", ""),
        patch.object(provider_settings, "MOCK_PROVIDER_RESPONSES", False),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
            json={"content": "What is the capital of France?"},
            headers=auth_headers,
        )

    assert resp.status_code == 503
    assert resp.json() == {
        "detail": "Provider 'groq' is not configured — missing API key."
    }


@pytest.mark.asyncio
async def test_clean_message_is_not_flagged(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
    db_session: AsyncSession,
) -> None:
    """A safe message passes the keyword filter and is sent to the provider."""
    async def _mock_stream(*args, **kwargs):
        yield "Hello!"

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
            json={"content": "What is the capital of France?"},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert MODERATION_RESPONSE not in resp.text

    result = await db_session.execute(select(FlaggedEvent))
    events = result.scalars().all()
    assert len(events) == 0


# ---------------------------------------------------------------------------
# Provider content policy filter tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_content_policy_error_returns_moderation_response(
    client, auth_headers, groq_conversation_id
):
    """Provider ContentPolicyError returns the moderation response as SSE."""
    async def _raises_policy(*args, **kwargs):
        raise ContentPolicyError("blocked")
        yield  # make it an async generator

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_raises_policy),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
            json={"content": "something the provider blocks"},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert MODERATION_RESPONSE in resp.text


@pytest.mark.asyncio
async def test_provider_content_policy_error_stores_event_with_provider_filter_type(
    client: AsyncClient,
    auth_headers: dict[str, str],
    groq_conversation_id: str,
    db_session: AsyncSession,
) -> None:
    blocked_content = "something the provider blocks"

    async def _raises_policy(*args, **kwargs):
        raise ContentPolicyError("blocked")
        yield

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_raises_policy),
    ):
        await client.post(
            f"/api/v1/chat/conversations/{groq_conversation_id}/messages/send",
            json={"content": blocked_content},
            headers=auth_headers,
        )

    result = await db_session.execute(select(FlaggedEvent))
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].filter_type == "provider"
    assert events[0].message_content == blocked_content
