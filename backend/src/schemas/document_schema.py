"""Pydantic schemas for document management endpoints.

Documents are admin-managed PDFs with role-based access control.
Each document specifies which roles are allowed to access its contents.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

UserRoleLiteral = Literal["user", "admin", "security"]


class DocumentOut(BaseModel):
    """Response schema for a single document."""
    id: str = Field(description="Document UUID.")
    title: str = Field(description="Human-readable document title.")
    description: str = Field(description="Optional description.")
    filename: str = Field(description="Original PDF filename.")
    file_size: int = Field(description="File size in bytes.")
    status: str = Field(description="Document status: active, processing, or archived.")
    uploaded_by: str = Field(description="UUID of the user who uploaded the document.")
    allowed_roles: list[UserRoleLiteral] = Field(description="Roles permitted to access this document.")
    chroma_doc_id: str | None = Field(description="Corresponding ChromaDB doc_id, if indexed.")
    created_at: datetime = Field(description="Timestamp when the document was created.")
    updated_at: datetime = Field(description="Timestamp of the last update.")

    model_config = {"from_attributes": True}


class DocumentUpdateRequest(BaseModel):
    """Request schema for updating document metadata or role assignments."""
    title: str | None = Field(default=None, description="Updated document title.")
    description: str | None = Field(default=None, description="Updated description.")
    allowed_roles: list[UserRoleLiteral] | None = Field(
        default=None, description="Updated list of roles permitted to access this document."
    )
    status: Literal["active", "archived", "processing"] | None = Field(
        default=None, description="Updated document status."
    )
