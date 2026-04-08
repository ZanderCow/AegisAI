"""HTTP router API endpoints for the chat feature.

This module acts strictly as the router (controller) layer, accepting
HTTP calls and transferring the payload to the ChatService.
No business logic or database queries should reside here.
"""
import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.rag import get_rag_service
from src.core.database import get_db
from src.schemas.chat_schema import (
    CreateConversationRequest,
    ConversationResponse,
    SendMessageRequest,
    MessageResponse,
)
from src.repo.conversation_repo import ConversationRepository
from src.repo.flagged_event_repo import FlaggedEventRepository
from src.service.chat_service import ChatService
from src.service.rag_service import RAGService
from src.security.jwt import get_current_user
from src.providers import validate_provider
from src.core.logger import get_logger

logger = get_logger("CHAT_API")

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(
    session: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(get_rag_service),
) -> ChatService:
    """Dependency injection factory for the ChatService layer.

    Args:
        session (AsyncSession): The injected database session dependency.
        rag (RAGService): The injected RAG service backed by the shared Chroma setup.

    Returns:
        ChatService: An initialized instance of the ChatService.
    """
    return ChatService(ConversationRepository(session), rag, FlaggedEventRepository(session))


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user),
):
    """Create a new conversation session with a locked provider and model.

    The provider and model are fixed for the lifetime of the conversation.
    All subsequent messages in this conversation will use the same provider.

    Args:
        request (CreateConversationRequest): Validated conversation creation
            payload from the client.
        service (ChatService): Injected chat service.
        user_id (str): Authenticated user identifier.

    Returns:
        ConversationResponse: Identifier for the newly created conversation.
    """
    logger.info(f"Received create conversation request from user {user_id}")
    conversation_id = await service.create_conversation(user_id, request)
    return ConversationResponse(conversation_id=conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages/send",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": (
                "Server-Sent Events (SSE) stream. Each line is `data: {\"content\": str, \"done\": bool}`; "
                "final event uses `done: true`. Swagger “Try it out” often cannot display streams—use curl or the app UI."
            ),
            "content": {
                "text/event-stream": {
                    "schema": {"type": "string", "example": 'data: {"content": "Hi", "done": false}\n\n'},
                }
            },
        },
    },
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user),
):
    """Send a message and receive a streaming AI response via Server-Sent Events.

    The conversation ownership is verified before the stream begins so that
    a 404 is returned cleanly before any SSE data is sent.

    Each SSE event has the shape: data: {"content": "...", "done": false}
    The final event is: data: {"content": "", "done": true}

    Args:
        conversation_id (str): Conversation identifier scoped to the current
            authenticated user.
        request (SendMessageRequest): Message payload to append and send.
        service (ChatService): Injected chat service.
        user_id (str): Authenticated user identifier.

    Returns:
        StreamingResponse: Server-sent event stream of assistant response
        chunks followed by a terminal done event.
    """
    logger.info(f"Received send message request for conversation {conversation_id}")
    convo = await service.get_conversation_or_404(conversation_id, user_id)
    validate_provider(convo.provider)

    async def event_stream():
        async for chunk in service.stream_response(convo, request.content):
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user),
):
    """Fetch the message history for a conversation.

    Returns an empty list if the conversation does not exist or does not
    belong to the authenticated user — conversation existence is not leaked.

    Args:
        conversation_id (str): Conversation identifier scoped to the current
            authenticated user.
        service (ChatService): Injected chat service.
        user_id (str): Authenticated user identifier.

    Returns:
        list[MessageResponse]: Ordered conversation history for the requested
        conversation, or an empty list when inaccessible.
    """
    logger.info(f"Received get messages request for conversation {conversation_id}")
    return await service.get_messages(conversation_id, user_id)
