"""Unit tests for deterministic mock provider behavior in E2E mode.

This module verifies that the provider layer can switch into the local mock
response path used by automated tests, allowing chat streaming behavior to be
validated without requiring live third-party model credentials.
"""
import pytest
from pytest import MonkeyPatch

from src.core.config import settings
from src.providers import stream_from_provider, validate_provider


@pytest.mark.asyncio
async def test_mock_provider_streams_uploaded_context(monkeypatch: MonkeyPatch) -> None:
    """Verify the mock provider streams answers grounded in uploaded context.

    This test enables deterministic mock responses, clears the Groq API key,
    and confirms that provider validation and streaming still succeed using the
    embedded document excerpt supplied in the system prompt.

    Args:
        monkeypatch (MonkeyPatch): Pytest fixture used to override runtime
            settings for mock-provider execution.
    """
    monkeypatch.setattr(settings, "MOCK_PROVIDER_RESPONSES", True)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    validate_provider("groq")

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "Use the following document excerpts as context to answer the user's question. "
                "If the context is not relevant, answer from your own knowledge.\n\n"
                "[Source: handbook.pdf]\nAegis handbook: The office Wi-Fi password is AEGIS-2026-SECURE."
            ),
        },
        {"role": "user", "content": "What is the office Wi-Fi password?"},
    ]

    chunks: list[str] = []
    async for chunk in stream_from_provider("groq", "llama-3.1-8b-instant", messages):
        chunks.append(chunk)

    response = "".join(chunks)
    assert "handbook.pdf" in response
    assert "AEGIS-2026-SECURE" in response
