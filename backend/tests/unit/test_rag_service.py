"""Unit tests for the remote Chroma-backed RAG service."""
from unittest.mock import AsyncMock, Mock

import pytest

from src.service.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_service_lists_documents_from_collection_metadata() -> None:
    """RAGService should transform chunk metadata into deduplicated document rows."""
    collection = AsyncMock()
    collection.get = AsyncMock(
        return_value={
            "metadatas": [
                {"doc_id": "doc-1", "filename": "handbook.pdf", "chunk_index": 0},
                {"doc_id": "doc-1", "filename": "handbook.pdf", "chunk_index": 1},
                {"doc_id": "doc-2", "filename": "policy.pdf", "chunk_index": 0},
            ]
        }
    )

    chroma = Mock()
    chroma.get_collection = AsyncMock(return_value=collection)
    chroma.unavailable_error = Mock(side_effect=lambda action, exc: RuntimeError(f"{action}: {exc}"))

    rag = RAGService(chroma=chroma)
    documents = await rag.list_documents("user-123")

    assert documents == [
        {"doc_id": "doc-1", "filename": "handbook.pdf", "chunk_count": 2},
        {"doc_id": "doc-2", "filename": "policy.pdf", "chunk_count": 1},
    ]
    chroma.get_collection.assert_awaited_once()
    collection.get.assert_awaited_once_with(
        where={"doc_id": {"$ne": ""}},
        include=["metadatas"],
    )


@pytest.mark.asyncio
async def test_get_context_returns_none_when_chroma_is_unavailable() -> None:
    """Chat retrieval should fail closed instead of crashing the request."""
    chroma = Mock()
    chroma.get_collection = AsyncMock(side_effect=Exception("chroma offline"))
    chroma.endpoint = "http://chroma:8000"
    chroma.reset = Mock()

    rag = RAGService(chroma=chroma)

    assert await rag.get_context(["doc-1", "doc-2"], "what is in my document?") is None
    chroma.reset.assert_called_once()
