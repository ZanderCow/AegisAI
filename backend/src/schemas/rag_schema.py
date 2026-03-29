"""Pydantic schemas for RAG API request and response shapes.

Schemas act as the validation layer between external client requests
and internal application services for the RAG feature.
"""
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    """Schema describing one indexed document."""

    doc_id: str = Field(description="Stable logical identifier for the indexed document.")
    filename: str = Field(description="Original filename supplied by the user during upload.")
    chunk_count: int = Field(description="Number of text chunks currently stored for the document.")


class UploadResponse(BaseModel):
    """Schema returned after a successful document upload."""

    doc_id: str = Field(description="Stable logical identifier assigned to the uploaded document.")
    filename: str = Field(description="Original filename supplied by the user during upload.")
    chunk_count: int = Field(description="Number of chunks extracted, embedded, and stored.")
    message: str = Field(description="Human-readable upload summary for the client UI.")


class EmbedRequest(BaseModel):
    """Schema for direct embedding generation."""

    input: str | list[str] = Field(
        description="One text input or a batch of text inputs to embed with the local model."
    )


class EmbedResponse(BaseModel):
    """Schema containing local embedding vectors."""

    embeddings: list[list[float]] = Field(
        description="Embedding vectors generated for each supplied text input."
    )
    model: str = Field(description="Embedding model identifier used to generate the vectors.")
