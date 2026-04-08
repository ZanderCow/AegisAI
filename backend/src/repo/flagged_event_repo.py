"""Repository layer for moderation alarm event persistence."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.flagged_event_model import Alarm
from src.core.logger import get_logger

logger = get_logger("ALARM_REPOSITORY")


class FlaggedEventRepository:
    """Repository handling persistence of moderation alarm events.

    Attributes:
        session (AsyncSession): The active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_event(
        self,
        user_id: str,
        conversation_id: str,
        message_content: str,
        filter_type: str,
        provider: str,
    ) -> Alarm:
        """Inserts a new alarm record into the database.

        Args:
            user_id (str): UUID string of the user who sent the message.
            conversation_id (str): UUID string of the conversation.
            message_content (str): The exact flagged user message.
            filter_type (str): 'keyword' or 'provider'.
            provider (str): The AI provider name.

        Returns:
            Alarm: The newly created record.
        """
        logger.info(
            f"Logging alarm: filter_type={filter_type} provider={provider} "
            f"user={user_id} conversation={conversation_id}"
        )
        event = Alarm(
            user_id=uuid.UUID(user_id),
            conversation_id=uuid.UUID(conversation_id),
            message_content=message_content,
            filter_type=filter_type,
            provider=provider,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_all_events(self) -> list[Alarm]:
        """Returns all alarm events ordered by creation time."""
        result = await self.session.execute(
            select(Alarm).order_by(Alarm.created_at)
        )
        return list(result.scalars().all())
