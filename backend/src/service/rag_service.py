"""RAG (Retrieval-Augmented Generation) service using ChromaDB.

Handles PDF ingestion, text chunking, local embedding via ChromaDB's
built-in ONNX embedding function, and semantic retrieval for injecting
context into chat completions.
"""
import asyncio
import uuid
from io import BytesIO
from typing import Optional

from pypdf import PdfReader

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("RAG_SERVICE")

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_COLLECTION_NAME = "rag_documents"
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 150

_embedding_fn = DefaultEmbeddingFunction()


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + _CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - _CHUNK_OVERLAP
    return chunks


async def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """Compute embeddings locally via ChromaDB's built-in ONNX model."""
    result = await asyncio.to_thread(_embedding_fn, texts)
    return [list(v) for v in result]


class RAGService:
    """Service for managing RAG document ingestion and retrieval.

    Uses a persistent ChromaDB collection keyed by user_id metadata
    so each user's documents are isolated during retrieval.
    """

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=_embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Internal sync helpers (run in thread pool to avoid blocking loop)
    # ------------------------------------------------------------------

    def _sync_add(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    def _sync_get(self, where: dict) -> dict:
        return self._collection.get(where=where, include=["metadatas"])

    def _sync_get_ids(self, where: dict) -> list[str]:
        result = self._collection.get(where=where, include=[])
        return result["ids"]

    def _sync_delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)

    def _sync_query(
        self,
        query_texts: list[str],
        n_results: int,
        where: dict,
    ) -> dict:
        # n_results must not exceed the number of docs in the filtered set
        ids_in_scope = self._sync_get_ids(where)
        if not ids_in_scope:
            return {"documents": [[]], "metadatas": [[]]}
        capped = min(n_results, len(ids_in_scope))
        return self._collection.query(
            query_texts=query_texts,
            n_results=capped,
            where=where,
            include=["documents", "metadatas"],
        )

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def add_document(
        self, user_id: str, filename: str, pdf_bytes: bytes
    ) -> dict:
        """Parse a PDF, chunk it, embed it, and store it in ChromaDB."""
        reader = PdfReader(BytesIO(pdf_bytes))
        full_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
        chunks = _chunk_text(full_text)
        if not chunks:
            raise ValueError("No extractable text found in the uploaded PDF.")

        doc_id = str(uuid.uuid4())
        logger.info(f"Storing {len(chunks)} chunks for doc {doc_id} (user {user_id})")

        ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
        metadatas = [
            {"user_id": user_id, "doc_id": doc_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]

        await asyncio.to_thread(self._sync_add, ids, chunks, metadatas)
        logger.info(f"Stored doc {doc_id} with {len(chunks)} chunks")
        return {"doc_id": doc_id, "filename": filename, "chunk_count": len(chunks)}

    async def list_documents(self, user_id: str) -> list[dict]:
        """Return a deduplicated list of documents for a user."""
        result = await asyncio.to_thread(self._sync_get, {"user_id": user_id})
        docs: dict[str, dict] = {}
        for meta in result.get("metadatas", []):
            doc_id = meta["doc_id"]
            if doc_id not in docs:
                docs[doc_id] = {"doc_id": doc_id, "filename": meta["filename"], "chunk_count": 0}
            docs[doc_id]["chunk_count"] += 1
        return list(docs.values())

    async def delete_document(self, user_id: str, doc_id: str) -> None:
        """Delete all chunks belonging to a document owned by the user."""
        ids = await asyncio.to_thread(
            self._sync_get_ids, {"user_id": user_id, "doc_id": doc_id}
        )
        if ids:
            await asyncio.to_thread(self._sync_delete, ids)
            logger.info(f"Deleted doc {doc_id} ({len(ids)} chunks) for user {user_id}")

    async def get_context(self, user_id: str, query: str, n_results: int = 5) -> Optional[str]:
        """Retrieve the most semantically relevant chunks for a query.

        Returns None if the user has no documents.
        """
        try:
            result = await asyncio.to_thread(
                self._sync_query, [query], n_results, {"user_id": user_id}
            )
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            if not docs:
                return None
            parts = [f"[Source: {m['filename']}]\n{d}" for d, m in zip(docs, metas)]
            return "\n\n---\n\n".join(parts)
        except Exception as exc:
            logger.warning(f"RAG context retrieval failed: {exc}")
            return None


# Module-level singleton — ChromaDB client should not be recreated per request
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Return the shared RAGService singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
