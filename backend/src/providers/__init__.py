"""AI provider dispatcher for streaming LLM responses.

This module routes streaming requests to the correct provider module
(Groq, Gemini, or DeepSeek) based on the conversation's locked provider.
"""
from fastapi import HTTPException, status

from src.providers import groq as _groq
from src.providers import gemini as _gemini
from src.providers import deepseek as _deepseek
from src.providers import mock_provider as _mock_provider
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("PROVIDERS")

_PROVIDER_MODULES = {
    "groq": (_groq, lambda: settings.GROQ_API_KEY),
    "gemini": (_gemini, lambda: settings.GEMINI_API_KEY),
    "deepseek": (_deepseek, lambda: settings.DEEPSEEK_API_KEY),
}


def validate_provider(provider: str) -> None:
    """Validates that the provider is known and its API key is configured.

    Call this BEFORE returning a StreamingResponse so errors can be raised
    as clean HTTP responses rather than mid-stream runtime errors.

    Args:
        provider (str): One of 'groq', 'gemini', or 'deepseek'.

    Raises:
        HTTPException: 400 if the provider is unknown.
        HTTPException: 503 if the provider's API key is not configured.
    """
    if provider not in _PROVIDER_MODULES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )
    if settings.MOCK_PROVIDER_RESPONSES:
        return
    _, get_key = _PROVIDER_MODULES[provider]
    if not get_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not configured — missing API key.",
        )


async def stream_from_provider(provider: str, model: str, messages: list[dict]):
    """Dispatches a streaming request to the specified AI provider.

    Assumes validate_provider() has already been called. Streams text chunks
    from the provider's response.

    Args:
        provider (str): One of 'groq', 'gemini', or 'deepseek'.
        model (str): The model name string to send to the provider.
        messages (list[dict]): List of {'role': ..., 'content': ...} dicts.

    Yields:
        str: Text chunks from the provider's streaming response.
    """
    if settings.MOCK_PROVIDER_RESPONSES:
        logger.info(f"Streaming from mock provider for provider={provider} model={model}")
        async for chunk in _mock_provider.stream(messages):
            yield chunk
        return

    module, get_key = _PROVIDER_MODULES[provider]
    api_key = get_key()
    logger.info(f"Streaming from provider={provider} model={model}")
    async for chunk in module.stream(messages, model, api_key):
        yield chunk
