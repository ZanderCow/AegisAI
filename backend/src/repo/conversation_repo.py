"""Repository layer for database operations on Conversations and Messages.

This module isolates all SQLAlchemy ORM queries related to the chat
feature from the rest of the application, following the layered architecture.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.conversation_model import Conversation, Message
from src.models.flagged_event_model import Alarm
from src.models.user_model import User
from src.core.logger import get_logger

logger = get_logger("CONVERSATION_REPOSITORY")


class ConversationRepository:
    """Repository handling all CRUD interactions for Conversation and Message models.

    Attributes:
        session (AsyncSession): The active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initializes the repository with a database session.

        Args:
            session (AsyncSession): The active async SQLAlchemy session.
        """
        self.session = session

    async def create_conversation(
        self, user_id: str, provider: str, model: str, title: str
    ) -> Conversation:
        """Inserts a new conversation record into the database.

        Args:
            user_id (str): The UUID string of the owning user.
            provider (str): The AI provider name.
            model (str): The model name locked for this conversation.
            title (str): The human-readable conversation title.

        Returns:
            Conversation: The newly created Conversation model.
        """
        logger.info(f"Creating conversation for user {user_id} with provider={provider} model={model}")
        convo = Conversation(
            user_id=uuid.UUID(user_id),
            provider=provider,
            model=model,
            title=title,
        )
        self.session.add(convo)
        await self.session.commit()
        await self.session.refresh(convo)
        logger.info(f"Conversation created: {convo.id}")
        return convo

    async def get_conversation(self, conversation_id: str, user_id: str) -> Conversation | None:
        """Retrieves a conversation by ID, verifying ownership.

        Returns None if the conversation does not exist or does not
        belong to the specified user.

        Args:
            conversation_id (str): The UUID string of the conversation.
            user_id (str): The UUID string of the requesting user.

        Returns:
            Conversation | None: The matching conversation or None.
        """
        logger.info(f"Fetching conversation {conversation_id} for user {user_id}")
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(conversation_id),
                Conversation.user_id == uuid.UUID(user_id),
            )
        )
        convo = result.scalars().first()
        if convo:
            logger.info(f"Conversation found: {convo.id}")
        else:
            logger.info("Conversation not found or not owned by user")
        return convo

    async def list_conversations(self, user_id: str) -> list[dict[str, object]]:
        """Retrieves all conversations for a user with sidebar summary metadata.

        Args:
            user_id (str): The UUID string of the owner.

        Returns:
            list[dict[str, object]]: Normalized sidebar rows ordered by the
            latest conversation activity.
        """
        logger.info(f"Listing conversations for user {user_id}")

        latest_msg_sub = (
            select(
                Message.conversation_id,
                Message.content.label("last_message"),
                func.row_number().over(
                    partition_by=Message.conversation_id,
                    order_by=(Message.created_at.desc(), Message.id.desc()),
                ).label("rn"),
            )
            .subquery()
        )

        activity_sub = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_activity_at"),
                func.count(Message.id).label("message_count"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        last_activity_expr = func.coalesce(
            activity_sub.c.last_activity_at,
            Conversation.created_at,
        )

        result = await self.session.execute(
            select(
                Conversation.id,
                Conversation.title,
                Conversation.provider,
                Conversation.model,
                Conversation.created_at,
                last_activity_expr.label("updated_at"),
                latest_msg_sub.c.last_message,
                func.coalesce(activity_sub.c.message_count, 0).label("message_count"),
            )
            .outerjoin(
                latest_msg_sub,
                (Conversation.id == latest_msg_sub.c.conversation_id)
                & (latest_msg_sub.c.rn == 1),
            )
            .outerjoin(activity_sub, Conversation.id == activity_sub.c.conversation_id)
            .where(Conversation.user_id == uuid.UUID(user_id))
            .order_by(last_activity_expr.desc(), Conversation.created_at.desc())
        )

        rows = [
            {
                "id": row.id,
                "title": row.title,
                "provider": row.provider,
                "model": row.model,
                "last_message": row.last_message,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "message_count": int(row.message_count or 0),
            }
            for row in result.all()
        ]
        logger.info(f"Retrieved {len(rows)} conversations for user {user_id}")
        return rows

    async def add_message(
        self, conversation_id: uuid.UUID, role: str, content: str
    ) -> Message:
        """Inserts a new message into a conversation.

        Args:
            conversation_id (uuid.UUID): The UUID of the parent conversation.
            role (str): The speaker role ('user', 'assistant', or 'system').
            content (str): The message content.

        Returns:
            Message: The newly created Message model.
        """
        logger.info(f"Adding {role} message to conversation {conversation_id}")
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.session.add(msg)
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )
        await self.session.commit()
        await self.session.refresh(msg)
        logger.info(f"Message added: {msg.id}")
        return msg

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Deletes a conversation and all associated messages.

        Args:
            conversation_id (str): The UUID string of the conversation to delete.
            user_id (str): The UUID string of the requesting user (owner).

        Returns:
            bool: True if deleted successfully, False if not found or not owned.
        """
        logger.info(f"Attempting to delete conversation {conversation_id} for user {user_id}")
        convo = await self.get_conversation(conversation_id, user_id)
        if not convo:
            return False

        await self.session.execute(
            delete(Alarm).where(Alarm.conversation_id == convo.id)
        )
        await self.session.execute(
            delete(Message).where(Message.conversation_id == convo.id)
        )
        await self.session.delete(convo)
        await self.session.commit()
        logger.info(f"Conversation {conversation_id} deleted successfully")
        return True

    async def get_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        """Retrieves all messages for a conversation ordered by creation time.

        Args:
            conversation_id (uuid.UUID): The UUID of the conversation.

        Returns:
            list[Message]: All messages in chronological order.
        """
        logger.info(f"Fetching messages for conversation {conversation_id}")
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = list(result.scalars().all())
        logger.info(f"Found {len(messages)} messages")
        return messages

    async def get_historic_chat_page(
        self,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict[str, object]]]:
        """Return a paginated page of persisted conversations across all users.

        Conversations are ordered by most recent activity, where activity is
        defined as the latest message timestamp or the conversation creation
        time when no messages exist yet.

        Args:
            limit (int): Maximum number of conversations to return.
            offset (int): Number of conversations to skip.

        Returns:
            tuple[int, list[dict[str, object]]]: Total conversation count and
            a page of normalized conversation metadata rows.
        """
        logger.info("Fetching historic chat page limit=%s offset=%s", limit, offset)
        total_result = await self.session.execute(
            select(func.count()).select_from(Conversation)
        )
        total = int(total_result.scalar_one() or 0)

        last_activity_expr = func.coalesce(
            func.max(Message.created_at),
            Conversation.created_at,
        )

        result = await self.session.execute(
            select(
                Conversation.id,
                Conversation.title,
                Conversation.user_id,
                User.email,
                Conversation.provider,
                Conversation.model,
                Conversation.created_at,
                last_activity_expr.label("last_activity_at"),
                func.count(Message.id).label("message_count"),
            )
            .join(User, Conversation.user_id == User.id)
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .group_by(
                Conversation.id,
                Conversation.title,
                Conversation.user_id,
                User.email,
                Conversation.provider,
                Conversation.model,
                Conversation.created_at,
            )
            .order_by(last_activity_expr.desc(), Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        rows = []
        for row in result.all():
            rows.append(
                {
                    "conversation_id": row.id,
                    "title": row.title,
                    "user_id": row.user_id,
                    "user_email": row.email,
                    "provider": row.provider,
                    "model": row.model,
                    "created_at": row.created_at,
                    "last_activity_at": row.last_activity_at,
                    "message_count": int(row.message_count or 0),
                }
            )

        logger.info("Historic chat page returned %s conversations", len(rows))
        return total, rows

    async def get_messages_for_conversations(
        self,
        conversation_ids: list[uuid.UUID],
    ) -> list[Message]:
        """Return all messages for the provided conversations in stable order.

        Args:
            conversation_ids (list[uuid.UUID]): Conversation identifiers to load.

        Returns:
            list[Message]: Messages ordered by conversation and creation time.
        """
        if not conversation_ids:
            return []

        logger.info("Fetching messages for %s conversations", len(conversation_ids))
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id.in_(conversation_ids))
            .order_by(Message.conversation_id, Message.created_at)
        )
        messages = list(result.scalars().all())
        logger.info("Found %s historic messages", len(messages))
        return messages

    async def get_historic_chat_summary(self) -> dict[str, int]:
        """Return top-line counts for the security historic chat dashboard."""
        logger.info("Fetching historic chat dashboard summary")
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)

        total_histories_result = await self.session.execute(
            select(func.count()).select_from(Conversation)
        )
        total_messages_result = await self.session.execute(
            select(func.count()).select_from(Message)
        )
        recent_activity_result = await self.session.execute(
            select(func.count()).select_from(Message).where(Message.created_at >= day_ago)
        )
        unique_users_result = await self.session.execute(
            select(func.count(func.distinct(Conversation.user_id))).select_from(Conversation)
        )

        return {
            "total_histories": int(total_histories_result.scalar_one() or 0),
            "total_messages": int(total_messages_result.scalar_one() or 0),
            "recent_activity": int(recent_activity_result.scalar_one() or 0),
            "unique_users": int(unique_users_result.scalar_one() or 0),
        }
