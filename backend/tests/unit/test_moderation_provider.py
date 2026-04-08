"""Unit tests for provider-level content policy error detection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.moderation.exceptions import ContentPolicyError


def _make_mock_response(status_code: int, body: bytes):
    """Helper to build a mock httpx response."""
    response = MagicMock()
    response.status_code = status_code
    response.aread = AsyncMock(return_value=body)
    response.raise_for_status = MagicMock()
    response.aiter_lines = AsyncMock(return_value=iter([]))
    return response


# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_groq_raises_content_policy_error_on_400_with_policy_marker():
    from src.providers.groq import stream

    body = b'{"error": {"type": "invalid_request_error", "code": "content_filter"}}'
    mock_response = _make_mock_response(400, body)

    async def mock_aiter_lines():
        return
        yield  # make it an async generator

    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.providers.groq.httpx.AsyncClient", return_value=mock_client_ctx):
        with pytest.raises(ContentPolicyError):
            async for _ in stream([{"role": "user", "content": "test"}], "model", "key"):
                pass


@pytest.mark.asyncio
async def test_groq_does_not_raise_content_policy_error_on_400_without_marker():
    from src.providers.groq import stream

    body = b'{"error": {"type": "invalid_request_error", "message": "Unknown model"}}'
    mock_response = _make_mock_response(400, body)
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("400", request=MagicMock(), response=MagicMock())
    )

    async def mock_aiter_lines():
        return
        yield

    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.providers.groq.httpx.AsyncClient", return_value=mock_client_ctx):
        with pytest.raises(httpx.HTTPStatusError):
            async for _ in stream([{"role": "user", "content": "test"}], "model", "key"):
                pass


# ---------------------------------------------------------------------------
# DeepSeek
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deepseek_raises_content_policy_error_on_400_with_policy_marker():
    from src.providers.deepseek import stream

    body = b'{"error": {"code": "content_policy", "message": "Content blocked"}}'
    mock_response = _make_mock_response(400, body)

    async def mock_aiter_lines():
        return
        yield

    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.providers.deepseek.httpx.AsyncClient", return_value=mock_client_ctx):
        with pytest.raises(ContentPolicyError):
            async for _ in stream([{"role": "user", "content": "test"}], "model", "key"):
                pass


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gemini_raises_content_policy_error_on_400_with_safety_marker():
    from src.providers.gemini import stream

    body = b'{"error": {"message": "Request blocked due to safety settings", "blockReason": "SAFETY"}}'
    mock_response = _make_mock_response(400, body)

    async def mock_aiter_lines():
        return
        yield

    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.providers.gemini.httpx.AsyncClient", return_value=mock_client_ctx):
        with pytest.raises(ContentPolicyError):
            async for _ in stream([{"role": "user", "content": "test"}], "model", "key"):
                pass
