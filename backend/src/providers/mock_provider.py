"""Deterministic mock LLM responses for end-to-end testing.

This provider is intentionally simple: it inspects the system prompt
constructed by the chat service and mirrors retrieved document context
back to the caller. That makes RAG assertions stable without requiring
external model credentials during E2E runs.
"""
from collections.abc import AsyncIterator


_SYSTEM_PREFIX = (
    "Use the following document excerpts as context to answer the user's question. "
    "If the context is not relevant, answer from your own knowledge."
)


def _extract_document_context(messages: list[dict]) -> str | None:
    """Return the injected document context from the leading system message."""
    for message in messages:
        if message.get("role") != "system":
            continue
        content = str(message.get("content", ""))
        if not content.startswith(_SYSTEM_PREFIX):
            continue
        _, _, context = content.partition("\n\n")
        normalized = " ".join(context.split())
        return normalized or None
    return None


def _latest_user_prompt(messages: list[dict]) -> str:
    """Return the most recent user message from a chat transcript."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", "")).strip()
    return ""


def _build_response(messages: list[dict]) -> str:
    """Generate a deterministic answer for E2E assertions."""
    context = _extract_document_context(messages)
    if context:
        return f"RAG answer based on uploaded documents: {context}"

    prompt = _latest_user_prompt(messages)
    if prompt:
        return f"No uploaded document context matched this request: {prompt}"

    return "No user prompt was provided."


async def stream(messages: list[dict], chunk_size: int = 48) -> AsyncIterator[str]:
    """Yield the mock response in chunks to mimic provider streaming."""
    response = _build_response(messages)
    for index in range(0, len(response), chunk_size):
        yield response[index:index + chunk_size]
