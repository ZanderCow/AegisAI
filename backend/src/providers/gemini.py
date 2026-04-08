"""Gemini provider — raw HTTP SSE streaming.

Google Gemini uses a different JSON structure and authentication model
compared to OpenAI-compatible providers. No SDKs are used; all
communication is raw HTTP via httpx.
"""
import json

import httpx

from src.core.logger import get_logger
from src.moderation.exceptions import ContentPolicyError

logger = get_logger("PROVIDER_GEMINI")

_CONTENT_POLICY_MARKERS = ("safety", "prohibited", "blockreason", "harm_category")

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"


def _to_gemini_contents(messages: list[dict]) -> list[dict]:
    """Converts OpenAI-style messages to Gemini's content format.

    Args:
        messages (list[dict]): List of {'role': ..., 'content': ...} dicts.

    Returns:
        list[dict]: Messages in Gemini's {'role': ..., 'parts': [...]} format.
    """
    result = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        result.append({"role": role, "parts": [{"text": m["content"]}]})
    return result


async def stream(messages: list[dict], model: str, api_key: str):
    """Streams a chat completion response from Google Gemini via raw HTTP SSE.

    Converts the message history to Gemini's format, sends the request,
    and yields text chunks as they arrive in the Server-Sent Events stream.

    Args:
        messages (list[dict]): List of {'role': ..., 'content': ...} dicts.
        model (str): The Gemini model name (e.g. 'gemini-2.0-flash-lite').
        api_key (str): The Google Gemini API key.

    Yields:
        str: Text content chunks from the streaming response.

    Raises:
        ContentPolicyError: If Gemini's safety filters block the request.
    """
    url = _BASE_URL.format(model=model)
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            url,
            params={"alt": "sse", "key": api_key},
            headers={"Content-Type": "application/json"},
            json={"contents": _to_gemini_contents(messages)},
        ) as response:
            if response.status_code == 400:
                body = (await response.aread()).decode("utf-8", errors="ignore").lower()
                if any(marker in body for marker in _CONTENT_POLICY_MARKERS):
                    raise ContentPolicyError("Gemini content policy violation")
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise httpx.HTTPStatusError(
                    f"Gemini API error: {e.response.status_code}",
                    request=e.request,
                    response=e.response,
                ) from None
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    if text:
                        yield text
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
