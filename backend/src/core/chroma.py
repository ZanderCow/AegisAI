"""Remote Chroma client setup and dependency wiring.

This module mirrors the role of ``database.py`` for the vector store:
it owns connection configuration, lazy initialization, and dependency
access for the shared Chroma collection used by the RAG pipeline.
"""
import asyncio

import chromadb
from chromadb.api.async_api import AsyncClientAPI, AsyncCollection
from chromadb.config import Settings as ChromaSettings

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("CHROMA_CORE")


class ChromaManager:
    """Manage lazy access to the configured remote Chroma collection.

    This class centralizes the connection lifecycle for the application's
    shared Chroma collection so endpoint and service layers do not need to
    manage client creation themselves.

    Attributes:
        _client (AsyncClientAPI | None): Cached remote Chroma HTTP client.
        _collection (AsyncCollection | None): Cached collection handle created
            from the configured collection name.
        _init_lock (asyncio.Lock): Lock preventing concurrent first-time
            initialization from racing during startup traffic.
    """

    def __init__(self) -> None:
        """Initialize an empty Chroma manager with no active connection."""
        self._client: AsyncClientAPI | None = None
        self._collection: AsyncCollection | None = None
        self._init_lock = asyncio.Lock()

    @property
    def endpoint(self) -> str:
        """Return the Chroma endpoint derived from application settings.

        Returns:
            str: Fully qualified HTTP or HTTPS endpoint for the configured
            Chroma server.
        """
        scheme = "https" if settings.CHROMA_SSL else "http"
        return f"{scheme}://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"

    def reset(self) -> None:
        """Drop cached connection state so the next access reconnects.

        This is used after transient Chroma failures so subsequent requests can
        attempt a clean reconnection path.
        """
        self._client = None
        self._collection = None

    def unavailable_error(self, action: str, exc: Exception) -> RuntimeError:
        """Build a consistent runtime error for Chroma availability failures.

        Args:
            action (str): Short label describing the failed Chroma operation.
            exc (Exception): The underlying exception raised by the Chroma
                client or collection call.

        Returns:
            RuntimeError: Normalized runtime error with endpoint guidance for
            callers and logs.
        """
        logger.warning(f"Chroma {action} failed against {self.endpoint}: {exc}")
        self.reset()
        return RuntimeError(
            f"Chroma is unavailable at {self.endpoint}. "
            "Check CHROMA_HOST, CHROMA_PORT, and CHROMA_SSL."
        )

    async def get_collection(self) -> AsyncCollection:
        """Return the configured Chroma collection, connecting lazily once.

        Returns:
            AsyncCollection: Shared Chroma collection handle for the configured
            collection name.

        Raises:
            RuntimeError: If the Chroma client cannot connect or the collection
            cannot be created or retrieved.
        """
        if self._collection is not None:
            return self._collection

        async with self._init_lock:
            if self._collection is not None:
                return self._collection

            try:
                logger.info(
                    "Connecting to remote Chroma collection "
                    f"{settings.CHROMA_COLLECTION_NAME} at {self.endpoint}"
                )
                self._client = await chromadb.AsyncHttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    ssl=settings.CHROMA_SSL,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._collection = await self._client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as exc:
                raise self.unavailable_error("connection", exc) from exc

            return self._collection


_chroma_manager: ChromaManager | None = None


def get_chroma_manager() -> ChromaManager:
    """Return the shared Chroma manager instance.

    Returns:
        ChromaManager: Process-wide Chroma manager used by dependency
        injection and service constructors.
    """
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager


def reset_chroma_manager() -> None:
    """Reset the shared manager, primarily for test isolation.

    This helper lets tests clear the cached singleton without needing to
    recreate the full application process.
    """
    global _chroma_manager
    if _chroma_manager is not None:
        _chroma_manager.reset()
    _chroma_manager = None
