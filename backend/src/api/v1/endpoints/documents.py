"""HTTP router for role-scoped document management.

Admins upload PDFs and assign allowed roles. Users can list documents
accessible to their own role. Security and admins can view all documents.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logger import get_logger
from src.repo.document_repo import DocumentRepository
from src.schemas.document_schema import DocumentOut, DocumentUpdateRequest
from src.security.jwt import get_current_user_with_role, AuthenticatedUser
from src.service.rag_service import get_rag_service, RAGService

logger = get_logger("DOCUMENTS_API")

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB

_ADMIN_ROLES = {"admin"}
_AUDIT_ROLES = {"admin", "security"}


def _require_role(auth: AuthenticatedUser, allowed: set[str]) -> None:
    """Raise 403 if the user's role is not in the allowed set."""
    if auth.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{auth.role}' is not permitted to perform this action.",
        )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(default=""),
    description: str = Form(default=""),
    allowed_roles: str = Form(default=""),  # comma-separated: "admin,it,hr"
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """Upload a PDF and assign which roles may access it.

    Only admin users may upload documents.

    - **file**: PDF file (max 20 MB).
    - **title**: Display title for the document.
    - **description**: Optional description.
    - **allowed_roles**: Comma-separated roles, e.g. ``admin,it,finance``.
    """
    _require_role(auth, _ADMIN_ROLES)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_PDF_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF exceeds the 20 MB size limit.",
        )

    roles = [r.strip() for r in allowed_roles.split(",") if r.strip()]
    doc_title = title or file.filename

    logger.info(f"Admin {auth.user_id} uploading '{file.filename}' roles={roles}")

    # Index in ChromaDB first to get a doc_id
    try:
        rag_result = await rag.add_document(
            user_id=auth.user_id,
            filename=file.filename,
            pdf_bytes=pdf_bytes,
            allowed_roles=roles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    # Persist metadata in PostgreSQL
    repo = DocumentRepository(db)
    doc = await repo.create(
        title=doc_title,
        description=description,
        filename=file.filename,
        file_size=len(pdf_bytes),
        uploaded_by=auth.user_id,
        allowed_roles=roles,
        chroma_doc_id=rag_result["doc_id"],
        status="active",
    )

    return _to_out(doc)


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
):
    """List documents accessible to the authenticated user's role.

    Admins and security officers see all documents.
    All other roles see only documents whose allowed_roles includes their role.
    """
    repo = DocumentRepository(db)
    if auth.role in _AUDIT_ROLES:
        docs = await repo.list_all()
    else:
        docs = await repo.list_by_role(auth.role)
    return [_to_out(d) for d in docs]


@router.put("/{doc_id}", response_model=DocumentOut)
async def update_document(
    doc_id: str,
    body: DocumentUpdateRequest,
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """Update document metadata or role assignments.

    Only admin users may update documents.
    When allowed_roles changes, the ChromaDB chunks are re-indexed with the
    new role flags so that RAG context filtering stays consistent.
    """
    _require_role(auth, _ADMIN_ROLES)

    repo = DocumentRepository(db)
    doc = await repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    updated = await repo.update(
        doc_id=doc_id,
        title=body.title,
        description=body.description,
        allowed_roles=[str(r) for r in body.allowed_roles] if body.allowed_roles is not None else None,
        status=body.status,
    )

    # If roles changed and the document is indexed in ChromaDB, re-index the chunks
    if body.allowed_roles is not None and updated and updated.chroma_doc_id:
        new_roles = [str(r) for r in body.allowed_roles]
        await rag.update_document_roles(updated.chroma_doc_id, new_roles)
        logger.info(f"Re-indexed ChromaDB roles for doc {doc_id}")

    return _to_out(updated)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
):
    """Delete a document and remove its chunks from the vector store.

    Only admin users may delete documents.
    """
    _require_role(auth, _ADMIN_ROLES)

    repo = DocumentRepository(db)
    doc = await repo.get_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chroma_id = doc.chroma_doc_id
    deleted = await repo.delete(doc_id)
    if deleted and chroma_id:
        await rag.delete_document(chroma_id)

    logger.info(f"Admin {auth.user_id} deleted document {doc_id}")


def _to_out(doc) -> DocumentOut:
    return DocumentOut(
        id=str(doc.id),
        title=doc.title,
        description=doc.description,
        filename=doc.filename,
        file_size=doc.file_size,
        status=doc.status,
        uploaded_by=str(doc.uploaded_by),
        allowed_roles=doc.allowed_roles or [],
        chroma_doc_id=doc.chroma_doc_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )
