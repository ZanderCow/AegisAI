"""SQLAlchemy ORM model for moderation alarm events.

Records every message blocked by either the keyword filter or a provider's
built-in content policy, along with contextual metadata for audit purposes.
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, Uuid, ForeignKey
from sqlalchemy.sql import func

from src.models.user_model import Base


class Alarm(Base):
    """Database model representing a moderation alarm event.

    Attributes:
        id (uuid.UUID): Primary key.
        user_id (uuid.UUID): FK to the user who sent the flagged message.
        conversation_id (uuid.UUID): FK to the conversation the message belongs to.
        message_content (str): The exact user message that was flagged.
        filter_type (str): Which layer caught it — 'keyword' or 'provider'.
        provider (str): The AI provider for the conversation.
        reason (str | None): Optional human-readable description (reserved for future use).
        created_at (datetime): Timestamp of the alarm event.
    """

    __tablename__ = "alarm"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    message_content = Column(Text, nullable=False)
    filter_type = Column(String(20), nullable=False)
    provider = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
