"""Groq provider — raw HTTP SSE streaming.

Groq uses the OpenAI-compatible chat completions API with Server-Sent Events.
No SDKs are used; all communication is raw HTTP via httpx.
"""
import json

import httpx

from src.core.logger import get_logger

logger = get_logger("PROVIDER_GROQ")

_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


async def stream(messages: list[dict], model: str, api_key: str):
    """Streams a chat completion response from Groq via raw HTTP SSE.

    Sends the message history to Groq and yields text chunks as they
    arrive in the Server-Sent Events stream.

    Args:
        messages (list[dict]): List of {'role': ..., 'content': ...} dicts.
        model (str): The Groq model name (e.g. 'llama-3.3-70b-versatile').
        api_key (str): The Groq API key.

    Yields:
        str: Text content chunks from the streaming response.
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
