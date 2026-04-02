"""RAG (Retrieval-Augmented Generation) service using ChromaDB.

Handles PDF ingestion, text chunking, local embedding via ChromaDB's
built-in ONNX embedding function, and semantic retrieval against a
remote Chroma collection for injecting context into chat completions.
"""
import asyncio
import uuid
from io import BytesIO

from chromadb.api.async_api import AsyncCollection
from pypdf import PdfReader

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from src.core.chroma import ChromaManager, get_chroma_manager
from src.core.logger import get_logger

logger = get_logger("RAG_SERVICE")

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 150

_embedding_fn = DefaultEmbeddingFunction()


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for retrieval.

    Args:
        text (str): Raw extracted document text.

    Returns:
        list[str]: Non-empty overlapping chunks suitable for embedding and
        semantic search.
    """
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
    """Compute embeddings locally via ChromaDB's built-in ONNX model.

    Args:
        texts (list[str]): Text inputs to embed in batch.

    Returns:
        list[list[float]]: Dense embedding vectors converted to plain floats.
    """
    result = await asyncio.to_thread(_embedding_fn, texts)
    return [[float(value) for value in v] for v in result]


def _document_where(user_id: str, doc_id: str) -> dict:
    """Build a Chroma filter matching a single user's document.

    Args:
        user_id (str): Authenticated user identifier.
        doc_id (str): Logical document identifier stored in metadata.

    Returns:
        dict: Chroma metadata filter limiting results to the requested
        user's document.
    """
    return {"$and": [{"user_id": user_id}, {"doc_id": doc_id}]}


class RAGService:
    """Service for managing RAG document ingestion and retrieval.

    This service owns document parsing, chunking, local embedding, and
    retrieval assembly. Connection management for the underlying Chroma
    collection is delegated to the injected ``ChromaManager``.

    Attributes:
        chroma (ChromaManager): Core-managed access point for the shared
            remote Chroma collection.
    """

    def __init__(self, chroma: ChromaManager | None = None) -> None:
        """Initialize the RAG service.

        Args:
            chroma (ChromaManager | None): Optional injected Chroma manager.
                When omitted, the shared application-level manager is used.
        """
        self.chroma = chroma or get_chroma_manager()

    async def _get_ids(self, collection: AsyncCollection, where: dict) -> list[str]:
        """Fetch matching Chroma record IDs for a metadata filter.

        Args:
            collection (AsyncCollection): Active Chroma collection handle.
            where (dict): Metadata filter sent to Chroma.

        Returns:
            list[str]: Matching vector record IDs.
        """
        result = await collection.get(where=where, include=[])
        return result["ids"]

    async def _query(
        self,
        collection: AsyncCollection,
        query: str,
        n_results: int,
        where: dict,
        include_restricted: bool = False,
    ) -> dict:
        """Run a filtered semantic search against the Chroma collection.

        Args:
            collection (AsyncCollection): Active Chroma collection handle.
            query (str): End-user query text to embed and search with.
            n_results (int): Maximum number of chunks to retrieve.
            where (dict): Metadata filter limiting the search scope.

        Returns:
            dict: Raw Chroma query payload containing matched documents and
            metadata lists.
        """
        # Non-privileged users only see non-restricted chunks
        if not include_restricted:
            effective_where = {"$and": [where, {"restricted": False}]}
        else:
            effective_where = dict(where)

        # n_results must not exceed the number of docs in the filtered set
        ids_in_scope = await self._get_ids(collection, effective_where)
        if not ids_in_scope:
            return {"documents": [[]], "metadatas": [[]]}

        capped = min(n_results, len(ids_in_scope))
        query_embeddings = await _get_embeddings([query])
        return await collection.query(
            query_embeddings=query_embeddings,
            n_results=capped,
            where=effective_where,
            include=["documents", "metadatas"],
        )

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def add_document(
        self, user_id: str, filename: str, pdf_bytes: bytes, restricted: bool = False
    ) -> dict:
        """Parse a PDF, chunk it, embed it, and store it in ChromaDB.

        Args:
            user_id (str): Authenticated user identifier used to partition
                document access.
            filename (str): Original uploaded filename.
            pdf_bytes (bytes): Raw PDF file contents.

        Returns:
            dict: Upload summary containing document ID, filename, and chunk
            count for the stored document.

        Raises:
            ValueError: If the PDF contains no extractable text.
            RuntimeError: If Chroma is unavailable during the write path.
        """
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
            {
                "user_id": user_id,
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "restricted": restricted,
            }
            for i in range(len(chunks))
        ]
        embeddings = await _get_embeddings(chunks)

        collection = await self.chroma.get_collection()
        try:
            await collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise self.chroma.unavailable_error("write", exc) from exc

        logger.info(f"Stored doc {doc_id} with {len(chunks)} chunks")
        return {"doc_id": doc_id, "filename": filename, "chunk_count": len(chunks), "restricted": restricted}

    async def list_documents(self, user_id: str) -> list[dict]:
        """Return a deduplicated list of documents for a user.

        Args:
            user_id (str): Authenticated user identifier whose documents are
                being listed.

        Returns:
            list[dict]: One row per logical document with filename and chunk
            count information.

        Raises:
            RuntimeError: If Chroma is unavailable during the read path.
        """
        collection = await self.chroma.get_collection()
        try:
            result = await collection.get(where={"user_id": user_id}, include=["metadatas"])
        except Exception as exc:
            raise self.chroma.unavailable_error("read", exc) from exc

        docs: dict[str, dict] = {}
        for meta in result.get("metadatas", []):
            doc_id = meta["doc_id"]
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta["filename"],
                    "chunk_count": 0,
                    "restricted": meta.get("restricted", False),
                }
            docs[doc_id]["chunk_count"] += 1
        return list(docs.values())

    async def delete_document(self, user_id: str, doc_id: str) -> None:
        """Delete all chunks belonging to a document owned by the user.

        Args:
            user_id (str): Authenticated user identifier.
            doc_id (str): Logical document identifier to remove.

        Raises:
            RuntimeError: If Chroma is unavailable during the delete path.
        """
        collection = await self.chroma.get_collection()
        try:
            ids = await self._get_ids(collection, _document_where(user_id, doc_id))
            if ids:
                await collection.delete(ids=ids)
                logger.info(f"Deleted doc {doc_id} ({len(ids)} chunks) for user {user_id}")
        except Exception as exc:
            raise self.chroma.unavailable_error("delete", exc) from exc

    async def get_context(self, user_id: str, query: str, user_role: str = "user", n_results: int = 5) -> str | None:
        """Retrieve the most semantically relevant chunks for a query.

        Retrieval failures intentionally fail closed so chat requests can
        continue even when the vector store is unavailable.

        Args:
            user_id (str): Authenticated user identifier used to scope search.
            query (str): End-user prompt used for semantic retrieval.
            n_results (int): Maximum number of document chunks to retrieve.

        Returns:
            str | None: Concatenated document context string when matches are
            found, otherwise ``None``.
        """
        from src.models.user_model import PRIVILEGED_ROLES
        include_restricted = user_role in PRIVILEGED_ROLES
        try:
            collection = await self.chroma.get_collection()
            result = await self._query(collection, query, n_results, {"user_id": user_id}, include_restricted)
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            if not docs:
                return None
            parts = [f"[Source: {m['filename']}]\n{d}" for d, m in zip(docs, metas)]
            return "\n\n---\n\n".join(parts)
        except Exception as exc:
            logger.warning(
                f"RAG context retrieval failed against {self.chroma.endpoint}: {exc}"
            )
            self.chroma.reset()
            return None
