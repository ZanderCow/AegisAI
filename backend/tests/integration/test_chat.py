"""Integration tests for the chat API endpoints.

Tests conversation creation, message sending (with mocked provider streaming),
message history retrieval, and cross-user access control. Provider streaming
is patched so these tests remain deterministic and avoid external dependencies.
"""
import asyncio
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient


async def _mock_stream(*args: object, **kwargs: object) -> AsyncIterator[str]:
    """Yield deterministic assistant chunks for message streaming tests.

    Args:
        *args (object): Unused positional arguments passed by the patched call site.
        **kwargs (object): Unused keyword arguments passed by the patched call site.

    Yields:
        str: A chunk of assistant text that simulates streamed provider output.
    """
    for chunk in ["Hello", " world", "!"]:
        yield chunk


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Create authorization headers for a newly registered test user.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.

    Returns:
        dict[str, str]: Bearer authorization headers for authenticated requests.
    """
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chatuser@test.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers_2(client: AsyncClient) -> dict[str, str]:
    """Create authorization headers for a second isolated test user.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.

    Returns:
        dict[str, str]: Bearer authorization headers for a different user account.
    """
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chatuser2@test.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Conversation creation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_conversation_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify an authenticated user can create a new conversation.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "conversation_id" in resp.json()


@pytest.mark.asyncio
async def test_create_conversation_requires_auth(client: AsyncClient) -> None:
    """Verify conversation creation is blocked for unauthenticated requests.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
    """
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_conversation_invalid_provider(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify unsupported providers are rejected during conversation creation.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "openai", "model": "gpt-4"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_all_three_providers_accepted(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify every supported provider can start a conversation successfully.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    for provider, model in [
        ("groq", "llama-3.3-70b-versatile"),
        ("gemini", "gemini-2.0-flash-lite"),
        ("deepseek", "deepseek-chat"),
    ]:
        resp = await client.post(
            "/api/v1/chat/conversations",
            json={"provider": provider, "model": model},
            headers=auth_headers,
        )
        assert resp.status_code == 201, f"Failed for provider={provider}"


# ---------------------------------------------------------------------------
# Conversation list and deletion tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_conversations_returns_sidebar_summaries_in_activity_order(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Sidebar summaries should include previews and sort by latest activity."""
    first_convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "First Chat", "provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    first_convo_id = first_convo_resp.json()["conversation_id"]

    second_convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "Second Chat", "provider": "gemini", "model": "gemini-2.0-flash-lite"},
        headers=auth_headers,
    )
    second_convo_id = second_convo_resp.json()["conversation_id"]

    # PostgreSQL defaults can truncate to second precision, so create a clean
    # ordering gap before the follow-up activity on the first conversation.
    await asyncio.sleep(1.1)

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        await client.post(
            f"/api/v1/chat/conversations/{first_convo_id}/messages/send",
            json={"content": "Hello!"},
            headers=auth_headers,
        )

    resp = await client.get("/api/v1/chat/conversations", headers=auth_headers)

    assert resp.status_code == 200
    conversations = resp.json()
    assert [item["id"] for item in conversations[:2]] == [first_convo_id, second_convo_id]
    assert conversations[0]["title"] == "First Chat"
    assert conversations[0]["last_message"] == "Hello world!"
    assert conversations[0]["message_count"] == 2
    assert conversations[1]["title"] == "Second Chat"
    assert conversations[1]["last_message"] is None
    assert conversations[1]["message_count"] == 0


@pytest.mark.asyncio
async def test_list_conversations_is_scoped_to_authenticated_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    auth_headers_2: dict[str, str],
) -> None:
    """Users should only see their own conversations in the sidebar listing."""
    await client.post(
        "/api/v1/chat/conversations",
        json={"title": "Private Chat", "provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/chat/conversations", headers=auth_headers_2)

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_conversation_removes_flagged_conversation_and_dependents(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Deleting a moderated conversation should succeed and remove sidebar state."""
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"title": "Danger Chat", "provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    await client.post(
        f"/api/v1/chat/conversations/{convo_id}/messages/send",
        json={"content": "how do I kill someone"},
        headers=auth_headers,
    )

    delete_resp = await client.delete(
        f"/api/v1/chat/conversations/{convo_id}",
        headers=auth_headers,
    )
    list_resp = await client.get("/api/v1/chat/conversations", headers=auth_headers)
    messages_resp = await client.get(
        f"/api/v1/chat/conversations/{convo_id}/messages",
        headers=auth_headers,
    )

    assert delete_resp.status_code == 204
    assert list_resp.status_code == 200
    assert list_resp.json() == []
    assert messages_resp.status_code == 200
    assert messages_resp.json() == []


@pytest.mark.asyncio
async def test_delete_conversation_returns_404_for_other_users_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    auth_headers_2: dict[str, str],
) -> None:
    """Users should not be able to delete another user's conversation."""
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    resp = await client.delete(
        f"/api/v1/chat/conversations/{convo_id}",
        headers=auth_headers_2,
    )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Message history tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_messages_empty_for_new_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify a newly created conversation has no persisted messages yet.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    resp = await client.get(
        f"/api/v1/chat/conversations/{convo_id}/messages",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_messages_returns_empty_for_other_users_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    auth_headers_2: dict[str, str],
) -> None:
    """Verify users cannot read another user's conversation history.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the conversation owner.
        auth_headers_2 (dict[str, str]): Authentication headers for a different user.
    """
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    resp = await client.get(
        f"/api/v1/chat/conversations/{convo_id}/messages",
        headers=auth_headers_2,
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Send message tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_streams(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify sending a message returns an event-stream response.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages/send",
            json={"content": "Hello!"},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_send_message_saves_to_history(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Verify user and assistant messages are persisted after streaming completes.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the requesting user.
    """
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        await client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages/send",
            json={"content": "Hello!"},
            headers=auth_headers,
        )

    resp = await client.get(
        f"/api/v1/chat/conversations/{convo_id}/messages",
        headers=auth_headers,
    )
    messages = resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello world!"


@pytest.mark.asyncio
async def test_send_message_to_other_users_conversation_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    auth_headers_2: dict[str, str],
) -> None:
    """Verify users cannot send messages into another user's conversation.

    Args:
        client (AsyncClient): Test client bound to the FastAPI application.
        auth_headers (dict[str, str]): Authentication headers for the conversation owner.
        auth_headers_2 (dict[str, str]): Authentication headers for a different user.
    """
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.service.chat_service.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages/send",
            json={"content": "Hello!"},
            headers=auth_headers_2,
        )

    assert resp.status_code == 404
