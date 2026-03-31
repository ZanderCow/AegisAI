"""Repository layer for database operations on Conversations and Messages.

This module isolates all SQLAlchemy ORM queries related to the chat
feature from the rest of the application, following the layered architecture.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.conversation_model import Alarm, Conversation, Message
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
        await self.session.commit()
        await self.session.refresh(msg)
        logger.info(f"Message added: {msg.id}")
        return msg

    async def add_alarm(self, message_id: uuid.UUID, reason: str) -> Alarm:
        """Inserts an alarm record for a flagged message.

        Args:
            message_id (uuid.UUID): The UUID of the flagged message.
            reason (str): Description of why the message was flagged.

        Returns:
            Alarm: The newly created Alarm record.
        """
        logger.info(f"Recording alarm for message {message_id}: {reason}")
        alarm = Alarm(message_id=message_id, reason=reason)
        self.session.add(alarm)
        await self.session.commit()
        await self.session.refresh(alarm)
        return alarm

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
