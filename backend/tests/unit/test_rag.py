"""Unit tests for core RAG setup and Chroma wiring."""
from unittest.mock import AsyncMock

import pytest

from src.core.chroma import ChromaManager
from src.core.config import settings


@pytest.mark.asyncio
async def test_rag_sets_up_chroma_collection_from_settings(monkeypatch) -> None:
    """The core RAG setup should lazily create and cache the configured collection."""
    collection = AsyncMock()

    client = AsyncMock()
    client.get_or_create_collection = AsyncMock(return_value=collection)

    async_client_factory = AsyncMock(return_value=client)
    monkeypatch.setattr("src.core.chroma.chromadb.AsyncHttpClient", async_client_factory)

    chroma = ChromaManager()

    async_client_factory.assert_not_called()

    first = await chroma.get_collection()
    second = await chroma.get_collection()

    assert first is collection
    assert second is collection
    async_client_factory.assert_awaited_once()
    assert async_client_factory.await_args.kwargs["host"] == settings.CHROMA_HOST
    assert async_client_factory.await_args.kwargs["port"] == settings.CHROMA_PORT
    assert async_client_factory.await_args.kwargs["ssl"] == settings.CHROMA_SSL
    assert async_client_factory.await_args.kwargs["settings"].anonymized_telemetry is False
    client.get_or_create_collection.assert_awaited_once_with(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
