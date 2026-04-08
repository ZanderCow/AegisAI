"""DeepSeek provider — raw HTTP SSE streaming.

DeepSeek uses the OpenAI-compatible chat completions API with Server-Sent Events.
No SDKs are used; all communication is raw HTTP via httpx.
"""
import json

import httpx

from src.core.logger import get_logger
from src.moderation.exceptions import ContentPolicyError

logger = get_logger("PROVIDER_DEEPSEEK")

_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

_CONTENT_POLICY_MARKERS = ("content_filter", "content_policy", "policy_violation", "moderation")


async def stream(messages: list[dict], model: str, api_key: str):
    """Streams a chat completion response from DeepSeek via raw HTTP SSE.

    Sends the message history to DeepSeek and yields text chunks as they
    arrive in the Server-Sent Events stream.

    Args:
        messages (list[dict]): List of {'role': ..., 'content': ...} dicts.
        model (str): The DeepSeek model name (e.g. 'deepseek-chat').
        api_key (str): The DeepSeek API key.

    Yields:
        str: Text content chunks from the streaming response.

    Raises:
        ContentPolicyError: If DeepSeek's content filter blocks the request.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            _BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "stream": True},
        ) as response:
            if response.status_code == 400:
                body = (await response.aread()).decode("utf-8", errors="ignore").lower()
                if any(marker in body for marker in _CONTENT_POLICY_MARKERS):
                    raise ContentPolicyError("DeepSeek content policy violation")
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                chunk = line[6:]
                if chunk.strip() == "[DONE]":
                    return
                try:
                    data = json.loads(chunk)
                    content = data["choices"][0]["delta"].get("content") or ""
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
