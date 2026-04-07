"""SQLAlchemy ORM model for the documents table.

Documents are uploaded by admins and assigned allowed roles.
Users may only access documents whose allowed_roles list includes their role.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Uuid, ARRAY, JSON, Text, ForeignKey, DateTime
from src.models.user_model import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Document(Base):
    """Database model for an admin-managed role-scoped document.

    Attributes:
        id (uuid.UUID): Primary key.
        title (str): Human-readable document title.
        description (str): Optional description.
        filename (str): Original PDF filename.
        file_size (int): File size in bytes.
        status (str): One of 'active', 'processing', 'archived'.
        uploaded_by (uuid.UUID): FK to the user who uploaded the document.
        allowed_roles (list[str]): Roles permitted to access this document.
        chroma_doc_id (str | None): Corresponding doc_id in the ChromaDB vector store.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
    """
    __tablename__ = "documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")
    uploaded_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    allowed_roles = Column(JSON, nullable=False, default=list)
    chroma_doc_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
