"""Endpoint-layer dependency factories for the RAG feature.

This module keeps FastAPI dependency wiring for RAG infrastructure out of the
route handlers so the endpoint layer stays thin and consistent.
"""
from fastapi import Depends

from src.core.chroma import ChromaManager, get_chroma_manager
from src.service.rag_service import RAGService


def get_rag_service(
    chroma: ChromaManager = Depends(get_chroma_manager),
) -> RAGService:
    """Create a RAG service wired to the shared core-managed Chroma setup.

    Args:
        chroma (ChromaManager): Shared Chroma dependency created from the core
            connection management layer.

    Returns:
        RAGService: Service instance ready to handle document ingestion and
        retrieval requests for the current application process.
    """
    return RAGService(chroma)
