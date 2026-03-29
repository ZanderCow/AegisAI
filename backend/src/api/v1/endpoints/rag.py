"""HTTP router for RAG (Retrieval-Augmented Generation) document management.

Endpoints allow authenticated users to upload PDFs, list their stored
documents, and delete documents from the ChromaDB vector store.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies.rag import get_rag_service
from src.schemas.rag_schema import (
    DocumentOut,
    UploadResponse,
    EmbedRequest,
    EmbedResponse,
)
from src.security.jwt import get_current_user
from src.service.rag_service import RAGService, _get_embeddings, _EMBEDDING_MODEL
from src.core.logger import get_logger

logger = get_logger("RAG_API")

router = APIRouter(prefix="/rag", tags=["rag"])

_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/embeddings", response_model=EmbedResponse)
async def create_embeddings(
    body: EmbedRequest,
    _: str = Depends(get_current_user),
):
    """Generate embeddings for one or more text inputs.

    Accepts a single string or a list of strings and returns the corresponding
    embedding vectors using the local all-MiniLM-L6-v2 ONNX model.

    Args:
        body (EmbedRequest): Input payload containing one or more texts to
            embed locally.
        _ (str): Authenticated user identifier injected for authorization.

    Returns:
        EmbedResponse: Embedding vectors along with the local model name.

    Raises:
        HTTPException: 422 if the input batch is empty.
        HTTPException: 502 if embedding generation fails unexpectedly.
    """
    texts = [body.input] if isinstance(body.input, str) else body.input
    if not texts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="input must not be empty.",
        )

    try:
        vectors = await _get_embeddings(texts)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return EmbedResponse(embeddings=vectors, model=_EMBEDDING_MODEL)


@router.post("/documents", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_service),
):
    """Upload a PDF and index it in the vector store.

    The file is chunked, embedded via the backend's local ONNX model, and
    persisted in ChromaDB keyed to the authenticated user.

    Args:
        file (UploadFile): Uploaded PDF payload to ingest.
        user_id (str): Authenticated user identifier owning the document.
        rag (RAGService): Injected RAG service handling parsing and storage.

    Returns:
        UploadResponse: Upload summary containing the stored document ID and
        chunk count.

    Raises:
        HTTPException: 413 if the PDF exceeds the size limit.
        HTTPException: 422 if the file is not a PDF or contains no usable text.
        HTTPException: 503 if the vector store is unavailable.
    """
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

    logger.info(f"User {user_id} uploading '{file.filename}' ({len(pdf_bytes)} bytes)")

    try:
        result = await rag.add_document(user_id, file.filename, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return UploadResponse(**result, message=f"Indexed {result['chunk_count']} chunks successfully.")


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    user_id: str = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_service),
):
    """Return all documents currently indexed for the authenticated user.

    Args:
        user_id (str): Authenticated user identifier.
        rag (RAGService): Injected RAG service handling document lookup.

    Returns:
        list[DocumentOut]: All logical documents currently indexed for the
        authenticated user.

    Raises:
        HTTPException: 503 if the vector store is unavailable.
    """
    try:
        return await rag.list_documents(user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_service),
):
    """Delete a document and all its indexed chunks.

    Only the document owner can delete their documents.

    Args:
        doc_id (str): Logical document identifier to delete.
        user_id (str): Authenticated user identifier.
        rag (RAGService): Injected RAG service handling vector deletion.

    Raises:
        HTTPException: 503 if the vector store is unavailable.
    """
    logger.info(f"User {user_id} deleting document {doc_id}")
    try:
        await rag.delete_document(user_id, doc_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
