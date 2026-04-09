"""Integration tests for the chat API endpoints.

Tests conversation creation, message sending (with mocked provider streaming),
message history retrieval, and cross-user access control. Provider streaming
is patched so these tests remain deterministic and avoid external dependencies.
"""
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
