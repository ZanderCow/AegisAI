"""Service layer for atomic document ingestion.

Owns the two-step Postgres → ChromaDB write so that no caller can
create a ChromaDB record without a corresponding Postgres row, and
vice-versa.
"""
from src.core.logger import get_logger
from src.models.document_model import Document
from src.repo.document_repo import DocumentRepository
from src.service.rag_service import RAGService

logger = get_logger("DOCUMENT_SERVICE")


class DocumentService:
    """Coordinates Postgres metadata and ChromaDB vector storage for documents.

    Attributes:
        doc_repo (DocumentRepository): Repository for the ``documents`` table.
        rag (RAGService): Service for ChromaDB ingestion and deletion.
    """

    def __init__(self, doc_repo: DocumentRepository, rag: RAGService) -> None:
        self.doc_repo = doc_repo
        self.rag = rag

    async def ingest_document(
        self,
        title: str,
        description: str,
        filename: str,
        pdf_bytes: bytes,
        uploaded_by: str,
        allowed_roles: list[str],
    ) -> Document:
        """Create a Postgres record and index the PDF in ChromaDB atomically.

        The Postgres record is created first to obtain a stable UUID that is
        used as the ChromaDB ``doc_id``.  If the ChromaDB write fails, the
        Postgres record is rolled back so the two stores stay in sync.

        Args:
            title (str): Display title for the document.
            description (str): Optional description.
            filename (str): Original PDF filename.
            pdf_bytes (bytes): Raw PDF content.
            uploaded_by (str): UUID of the uploading user.
            allowed_roles (list[str]): Roles permitted to access this document.

        Returns:
            Document: The newly created and persisted document record.

        Raises:
            ValueError: If the PDF contains no extractable text.
            RuntimeError: If ChromaDB is unavailable during the write path.
        """
        doc = await self.doc_repo.create(
            title=title,
            description=description,
            filename=filename,
            file_size=len(pdf_bytes),
            uploaded_by=uploaded_by,
            allowed_roles=allowed_roles,
            status="processing",
        )
        logger.info(f"Created document record {doc.id} for '{filename}'")

        try:
            await self.rag.add_document(
                doc_id=str(doc.id),
                filename=filename,
                pdf_bytes=pdf_bytes,
            )
        except Exception:
            logger.error(f"ChromaDB ingestion failed for doc {doc.id} — rolling back Postgres record")
            await self.doc_repo.delete(str(doc.id))
            raise

        updated = await self.doc_repo.update(str(doc.id), status="active", chroma_doc_id=str(doc.id))
        logger.info(f"Document {doc.id} ingested successfully")
        return updated or doc
