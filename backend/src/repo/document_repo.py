"""Repository layer for database operations on the documents table."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document_model import Document
from src.core.logger import get_logger

logger = get_logger("DOCUMENT_REPOSITORY")


class DocumentRepository:
    """Handles all CRUD interactions for the Document database model."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        title: str,
        description: str,
        filename: str,
        file_size: int,
        uploaded_by: str,
        allowed_roles: list[str],
        chroma_doc_id: str | None = None,
        status: str = "active",
    ) -> Document:
        """Insert a new document record."""
        doc = Document(
            title=title,
            description=description,
            filename=filename,
            file_size=file_size,
            uploaded_by=uuid.UUID(uploaded_by),
            allowed_roles=allowed_roles,
            chroma_doc_id=chroma_doc_id,
            status=status,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        logger.info(f"Created document {doc.id} ({filename})")
        return doc

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Fetch a document by UUID."""
        result = await self.session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        return result.scalars().first()

    async def list_all(self) -> list[Document]:
        """Return every document (admin / security use)."""
        result = await self.session.execute(select(Document).order_by(Document.id))
        return list(result.scalars().all())

    async def list_by_role(self, role: str) -> list[Document]:
        """Return documents whose allowed_roles array contains the given role."""
        result = await self.session.execute(
            select(Document)
            .where(Document.allowed_roles.any(role))  # PostgreSQL array ANY
            .order_by(Document.id)
        )
        return list(result.scalars().all())

    async def update(
        self,
        doc_id: str,
        title: str | None = None,
        description: str | None = None,
        allowed_roles: list[str] | None = None,
        status: str | None = None,
    ) -> Document | None:
        """Partially update a document record."""
        doc = await self.get_by_id(doc_id)
        if doc is None:
            return None
        if title is not None:
            doc.title = title
        if description is not None:
            doc.description = description
        if allowed_roles is not None:
            doc.allowed_roles = allowed_roles
        if status is not None:
            doc.status = status
        await self.session.commit()
        await self.session.refresh(doc)
        logger.info(f"Updated document {doc_id}")
        return doc

    async def delete(self, doc_id: str) -> bool:
        """Delete a document record. Returns True if it existed."""
        doc = await self.get_by_id(doc_id)
        if doc is None:
            return False
        await self.session.delete(doc)
        await self.session.commit()
        logger.info(f"Deleted document {doc_id}")
        return True
