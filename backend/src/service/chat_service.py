"""Service layer containing business logic for the chat feature.

This module orchestrates conversation creation, message persistence,
and streaming AI responses from the configured provider.
"""
from collections.abc import AsyncIterator
from collections import defaultdict

from fastapi import HTTPException, status

from src.schemas.chat_schema import (
    CreateConversationRequest,
    ConversationListItemResponse,
    HistoricChatDashboardQuery,
    HistoricChatDashboardResponse,
    HistoricChatDashboardSummaryResponse,
    HistoricChatHistoryItemResponse,
    HistoricChatMessageResponse,
    SecurityAlarmEventResponse,
)
from src.repo.conversation_repo import ConversationRepository
from src.repo.document_repo import DocumentRepository
from src.repo.flagged_event_repo import FlaggedEventRepository
from src.models.conversation_model import Conversation
from src.providers import stream_from_provider, validate_provider
from src.service.rag_service import RAGService
from src.moderation.keyword_filter import is_harmful, MODERATION_RESPONSE
from src.moderation.exceptions import ContentPolicyError
from src.core.logger import get_logger

logger = get_logger("CHAT_SERVICE")

SUPPORTED_PROVIDERS = {"groq", "gemini", "deepseek"}


class ChatService:
    """Service layer holding all chat business logic.

    Attributes:
        repo (ConversationRepository): The injected repository for database access.
        rag (RAGService): Injected RAG service used to enrich prompts with
            document context when available.
    """

    def __init__(
        self,
        repo: ConversationRepository,
        rag: RAGService,
        flagged_event_repo: FlaggedEventRepository,
        doc_repo: DocumentRepository | None = None,
    ) -> None:
        """Initialize the chat service.

        Args:
            repo (ConversationRepository): Repository handling conversation
                and message persistence.
            rag (RAGService): Service responsible for document retrieval and
                context assembly for chat prompts.
            flagged_event_repo (FlaggedEventRepository): Repository for logging
                moderation-flagged events.
            doc_repo (DocumentRepository): Repository used to resolve which
                documents the requesting user's role may access for RAG.
        """
        self.repo = repo
        self.rag = rag
        self.flagged_event_repo = flagged_event_repo
        self.doc_repo = doc_repo

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

    async def list_conversations(self, user_id: str) -> list[ConversationListItemResponse]:
        """Return sidebar-ready conversation summaries for the authenticated user.

        Args:
            user_id (str): The UUID string of the requesting user.

        Returns:
            list[ConversationListItemResponse]: Conversation summaries ordered
            by most recent activity first.
        """
        rows = await self.repo.list_conversations(user_id)
        return [
            ConversationListItemResponse(
                id=str(row["id"]),
                title=str(row["title"]),
                provider=str(row["provider"]),
                model=str(row["model"]),
                last_message=(
                    None if row["last_message"] is None else str(row["last_message"])
                ),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                message_count=int(row["message_count"]),
            )
            for row in rows
        ]

    async def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        """Delete a conversation owned by the authenticated user.

        Args:
            conversation_id (str): The UUID string of the conversation to remove.
            user_id (str): The UUID string of the requesting user.

        Raises:
            HTTPException: 404 if the conversation is missing or not owned by the user.
        """
        deleted = await self.repo.delete_conversation(conversation_id, user_id)
        if not deleted:
            logger.warning(f"Conversation {conversation_id} not found for delete by user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    async def stream_response(
        self, convo: Conversation, content: str, role: str = "user"
    ) -> AsyncIterator[str]:
        """Prepare and return a response stream for a chat message.

        Runs keyword moderation before calling the provider. If the message is
        flagged (keyword or provider content policy), logs the event, saves
        "That's Dangerous" as the assistant reply, and yields it without making
        or completing a provider API call.

        Provider validation is performed before returning the stream so safe
        messages still fail as clean HTTP errors instead of mid-stream.
        The conversation ownership must be verified by the caller BEFORE
        invoking this method.

        Args:
            convo (Conversation): The verified conversation model.
            content (str): The user's message content.
            role (str): The authenticated user's role for RAG document filtering.

        Returns:
            AsyncIterator[str]: Text chunks from the provider's streaming
            response, or the moderation response if the message is flagged.
        """
        logger.info(f"Streaming response for conversation {convo.id} provider={convo.provider}")

        # Layer 1: keyword filter — block before calling the provider
        if is_harmful(content):
            logger.warning(f"Keyword filter triggered for conversation {convo.id}")
            await self.flagged_event_repo.log_event(
                str(convo.user_id), str(convo.id), content, "keyword", convo.provider
            )
            await self.repo.add_message(convo.id, "user", content)
            await self.repo.add_message(convo.id, "assistant", MODERATION_RESPONSE)

            async def moderation_response() -> AsyncIterator[str]:
                yield MODERATION_RESPONSE

            return moderation_response()

        validate_provider(convo.provider)

        await self.repo.add_message(convo.id, "user", content)

        all_messages = await self.repo.get_messages(convo.id)
        messages_payload = [{"role": m.role, "content": m.content} for m in all_messages]

        # Inject RAG context — resolve allowed doc IDs from Postgres then query ChromaDB
        allowed_doc_ids: list[str] = []
        if self.doc_repo is not None:
            allowed_docs = await self.doc_repo.list_by_role(role)
            allowed_doc_ids = [str(d.chroma_doc_id) for d in allowed_docs if d.chroma_doc_id]
        rag_context = await self.rag.get_context(allowed_doc_ids, content)
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

        async def provider_response() -> AsyncIterator[str]:
            full_response = ""
            try:
                async for chunk in stream_from_provider(
                    convo.provider, convo.model, messages_payload
                ):
                    full_response += chunk
                    yield chunk
            except ContentPolicyError:
                # Layer 2: provider content policy — block after provider rejects
                logger.warning(f"Provider content policy triggered for conversation {convo.id}")
                await self.flagged_event_repo.log_event(
                    str(convo.user_id), str(convo.id), content, "provider", convo.provider
                )
                await self.repo.add_message(convo.id, "assistant", MODERATION_RESPONSE)
                yield MODERATION_RESPONSE
                return

            await self.repo.add_message(convo.id, "assistant", full_response)
            logger.info(
                f"Response complete for conversation {convo.id} — {len(full_response)} chars"
            )

        return provider_response()

    async def get_security_chat_histories(
        self,
        query: HistoricChatDashboardQuery,
    ) -> HistoricChatDashboardResponse:
        """Return paginated historic chat data for the security dashboard.

        Args:
            query (HistoricChatDashboardQuery): Applied pagination controls.

        Returns:
            HistoricChatDashboardResponse: Ordered conversation histories and
            summary metrics for the dashboard UI.
        """
        total, conversation_rows = await self.repo.get_historic_chat_page(
            limit=query.limit,
            offset=query.offset,
        )
        conversation_ids = [row["conversation_id"] for row in conversation_rows]
        messages = await self.repo.get_messages_for_conversations(conversation_ids)
        summary = await self.repo.get_historic_chat_summary()

        messages_by_conversation: dict[str, list[HistoricChatMessageResponse]] = defaultdict(list)
        for message in messages:
            messages_by_conversation[str(message.conversation_id)].append(
                HistoricChatMessageResponse(
                    id=str(message.id),
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                )
            )

        items = [
            HistoricChatHistoryItemResponse(
                conversation_id=str(row["conversation_id"]),
                title=str(row["title"]),
                user_id=str(row["user_id"]),
                user_email=str(row["user_email"]),
                provider=str(row["provider"]),
                model=str(row["model"]),
                created_at=row["created_at"],
                last_activity_at=row["last_activity_at"],
                message_count=int(row["message_count"]),
                messages=messages_by_conversation[str(row["conversation_id"])],
            )
            for row in conversation_rows
        ]

        return HistoricChatDashboardResponse(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
            summary=HistoricChatDashboardSummaryResponse(**summary),
        )

    async def get_security_alarm_events(self) -> list[SecurityAlarmEventResponse]:
        """Return persisted moderation alarms for the live security flagging dashboard."""
        rows = await self.flagged_event_repo.get_dashboard_events()
        return [
            SecurityAlarmEventResponse(
                id=str(row["id"]),
                user_id=str(row["user_id"]),
                user_email=str(row["user_email"]),
                conversation_id=str(row["conversation_id"]),
                message_content=str(row["message_content"]),
                filter_type=str(row["filter_type"]),
                provider=str(row["provider"]),
                reason=row["reason"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
