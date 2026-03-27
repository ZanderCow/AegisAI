"""Service layer containing business logic for the chat feature.

This module orchestrates conversation creation, message persistence,
and streaming AI responses from the configured provider.
"""
from fastapi import HTTPException, status

from src.schemas.chat_schema import CreateConversationRequest
from src.repo.conversation_repo import ConversationRepository
from src.models.conversation_model import Conversation
from src.providers import stream_from_provider
from src.service.rag_service import RAGService, get_rag_service
from src.core.logger import get_logger

logger = get_logger("CHAT_SERVICE")

SUPPORTED_PROVIDERS = {"groq", "gemini", "deepseek"}


class ChatService:
    """Service layer holding all chat business logic.

    Attributes:
        repo (ConversationRepository): The injected repository for database access.
    """

    def __init__(self, repo: ConversationRepository, rag: RAGService | None = None) -> None:
        """Initializes the service with a conversation repository instance."""
        self.repo = repo
        self.rag = rag or get_rag_service()

    async def create_conversation(
        self, user_id: str, request: CreateConversationRequest
    ) -> str:
        """Creates a new conversation with a locked provider and model.

        Args:
            user_id (str): The UUID string of the authenticated user.
            request (CreateConversationRequest): The validated request schema.

        Returns:
            str: The UUID string of the newly created conversation.

        Raises:
            HTTPException: 400 if the provider is not supported.
        """
        logger.info(f"Creating conversation for user {user_id} provider={request.provider}")
        if request.provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider '{request.provider}'. Choose from: {sorted(SUPPORTED_PROVIDERS)}",
            )
        convo = await self.repo.create_conversation(
            user_id=user_id,
            provider=request.provider,
            model=request.model,
            title=request.title,
        )
        return str(convo.id)

    async def get_conversation_or_404(
        self, conversation_id: str, user_id: str
    ) -> Conversation:
        """Fetches a conversation by ID, raising 404 if not found or not owned.

        Args:
            conversation_id (str): The UUID string of the conversation.
            user_id (str): The UUID string of the requesting user.

        Returns:
            Conversation: The verified conversation model.

        Raises:
            HTTPException: 404 if the conversation does not exist or is not owned by the user.
        """
        convo = await self.repo.get_conversation(conversation_id, user_id)
        if not convo:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return convo

    async def get_messages(self, conversation_id: str, user_id: str) -> list[dict]:
        """Returns the message history for a conversation.

        Returns an empty list if the conversation does not exist or is not
        owned by the user — does not leak conversation existence.

        Args:
            conversation_id (str): The UUID string of the conversation.
            user_id (str): The UUID string of the requesting user.

        Returns:
            list[dict]: List of {'role': ..., 'content': ...} dicts in order.
        """
        convo = await self.repo.get_conversation(conversation_id, user_id)
        if not convo:
            logger.info(f"No conversation {conversation_id} found for user {user_id} — returning empty list")
            return []
        messages = await self.repo.get_messages(convo.id)
        return [{"role": m.role, "content": m.content} for m in messages]

    async def stream_response(self, convo: Conversation, content: str):
        """Persists the user message, streams the provider response, then saves it.

        This is an async generator. The conversation ownership must be verified
        by the caller BEFORE invoking this method.

        Args:
            convo (Conversation): The verified conversation model.
            content (str): The user's message content.

        Yields:
            str: Text chunks from the provider's streaming response.
        """
        logger.info(f"Streaming response for conversation {convo.id} provider={convo.provider}")
        await self.repo.add_message(convo.id, "user", content)

        all_messages = await self.repo.get_messages(convo.id)
        messages_payload = [{"role": m.role, "content": m.content} for m in all_messages]

        # Inject RAG context as a leading system message if relevant documents exist
        rag_context = await self.rag.get_context(str(convo.user_id), content)
        if rag_context:
            system_msg = {
                "role": "system",
                "content": (
                    "Use the following document excerpts as context to answer the user's question. "
                    "If the context is not relevant, answer from your own knowledge.\n\n"
                    f"{rag_context}"
                ),
            }
            messages_payload = [system_msg] + messages_payload
            logger.info(f"Injected RAG context ({len(rag_context)} chars) for conversation {convo.id}")

        full_response = ""
        async for chunk in stream_from_provider(convo.provider, convo.model, messages_payload):
            full_response += chunk
            yield chunk

        await self.repo.add_message(convo.id, "assistant", full_response)
        logger.info(f"Response complete for conversation {convo.id} — {len(full_response)} chars")
