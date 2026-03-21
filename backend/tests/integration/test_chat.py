"""Integration tests for the chat API endpoints.

Tests conversation creation, message sending (with mocked provider streaming),
message history retrieval, and cross-user access control.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch


async def _mock_stream(*args, **kwargs):
    """Async generator that yields fixed chunks for testing."""
    for chunk in ["Hello", " world", "!"]:
        yield chunk


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Returns auth headers for a freshly signed-up user."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chatuser@test.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers_2(client: AsyncClient) -> dict:
    """Returns auth headers for a second freshly signed-up user."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chatuser2@test.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Conversation creation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_conversation_success(client, auth_headers):
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "conversation_id" in resp.json()


@pytest.mark.asyncio
async def test_create_conversation_requires_auth(client):
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_conversation_invalid_provider(client, auth_headers):
    resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "openai", "model": "gpt-4"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_all_three_providers_accepted(client, auth_headers):
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
async def test_get_messages_empty_for_new_conversation(client, auth_headers):
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
async def test_get_messages_returns_empty_for_other_users_conversation(client, auth_headers, auth_headers_2):
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
async def test_send_message_streams(client, auth_headers):
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.api.v1.endpoints.chat.validate_provider", return_value=None),
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
async def test_send_message_saves_to_history(client, auth_headers):
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.api.v1.endpoints.chat.validate_provider", return_value=None),
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
async def test_send_message_to_other_users_conversation_returns_404(client, auth_headers, auth_headers_2):
    convo_resp = await client.post(
        "/api/v1/chat/conversations",
        json={"provider": "groq", "model": "llama-3.3-70b-versatile"},
        headers=auth_headers,
    )
    convo_id = convo_resp.json()["conversation_id"]

    with (
        patch("src.api.v1.endpoints.chat.validate_provider", return_value=None),
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream),
    ):
        resp = await client.post(
            f"/api/v1/chat/conversations/{convo_id}/messages/send",
            json={"content": "Hello!"},
            headers=auth_headers_2,
        )

    assert resp.status_code == 404
