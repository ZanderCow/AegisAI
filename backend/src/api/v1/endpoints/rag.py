"""HTTP router for RAG (Retrieval-Augmented Generation) embeddings utility.

The document upload/list/delete endpoints have moved to /api/v1/documents
and are now role-scoped. This router retains the embeddings endpoint for
generating raw embedding vectors.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from src.schemas.rag_schema import EmbedRequest, EmbedResponse
from src.security.jwt import get_current_user
from src.service.rag_service import _get_embeddings, _EMBEDDING_MODEL
from src.core.logger import get_logger

logger = get_logger("RAG_API")

router = APIRouter(prefix="/rag", tags=["rag"])


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
