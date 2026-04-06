"""HTTP router API endpoints for the chat feature.

This module acts strictly as the router (controller) layer, accepting
HTTP calls and transferring the payload to the ChatService.
No business logic or database queries should reside here.
"""
import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.chat_schema import (
    CreateConversationRequest,
    ConversationResponse,
    SendMessageRequest,
    MessageResponse,
)
from src.repo.conversation_repo import ConversationRepository
from src.service.chat_service import ChatService
from src.security.jwt import get_current_user_with_role, AuthenticatedUser
from src.providers import validate_provider
from src.core.logger import get_logger

logger = get_logger("CHAT_API")

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(session: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency injection factory for the ChatService layer.

    Args:
        session (AsyncSession): The injected database session dependency.

    Returns:
        ChatService: An initialized instance of the ChatService.
    """
    return ChatService(ConversationRepository(session))


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    service: ChatService = Depends(get_chat_service),
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
):
    """Create a new conversation session with a locked provider and model.

    The provider and model are fixed for the lifetime of the conversation.
    All subsequent messages in this conversation will use the same provider.
    """
    logger.info(f"Received create conversation request from user {auth.user_id}")
    conversation_id = await service.create_conversation(auth.user_id, request)
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
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
):
    """Send a message and receive a streaming AI response via Server-Sent Events.

    The conversation ownership is verified before the stream begins so that
    a 404 is returned cleanly before any SSE data is sent.

    Each SSE event has the shape: data: {"content": "...", "done": false}
    The final event is: data: {"content": "", "done": true}
    """
    logger.info(f"Received send message request for conversation {conversation_id}")
    convo = await service.get_conversation_or_404(conversation_id, auth.user_id)
    validate_provider(convo.provider)

    async def event_stream():
        async for chunk in service.stream_response(convo, request.content, auth.role):
            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service),
    auth: AuthenticatedUser = Depends(get_current_user_with_role),
):
    """Fetch the message history for a conversation.

    Returns an empty list if the conversation does not exist or does not
    belong to the authenticated user — conversation existence is not leaked.
    """
    logger.info(f"Received get messages request for conversation {conversation_id}")
    return await service.get_messages(conversation_id, auth.user_id)
