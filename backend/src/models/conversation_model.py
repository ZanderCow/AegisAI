"""SQLAlchemy ORM models for conversations and messages.

This module defines the Conversation and Message models representing
AI chat sessions and their individual message exchanges.
"""
import uuid
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, BigInteger, Integer, Uuid, Boolean
from sqlalchemy.sql import func

from src.models.user_model import Base


class Conversation(Base):
    """Database model representing an AI chat conversation session.

    Attributes:
        id (uuid.UUID): The primary UUID key for the conversation.
        display_id (int | None): BIGSERIAL display ID (PostgreSQL only; None in SQLite tests).
        title (str): The human-readable title of the conversation.
        user_id (uuid.UUID): Foreign key linking the conversation to its owner.
        provider (str): The AI provider locked at creation (groq, gemini, deepseek).
        model (str): The model name locked at creation.
        tokens_used (int): Cumulative token count across all messages.
        created_at (datetime): Timestamp of conversation creation.
        updated_at (datetime): Timestamp of last conversation update.
    """

    __tablename__ = "conversations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_id = Column(BigInteger, nullable=True)  # BIGSERIAL in PostgreSQL; NULL in SQLite tests
    title = Column(String(255), nullable=False, default="New Chat")
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    tokens_used = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Message(Base):
    """Database model representing a single message within a conversation.

    Attributes:
        id (uuid.UUID): The primary UUID key for the message.
        display_id (int | None): BIGSERIAL display ID (PostgreSQL only; None in SQLite tests).
        conversation_id (uuid.UUID): Foreign key linking the message to its conversation.
        role (str): The speaker role — one of 'user', 'assistant', or 'system'.
        content (str): The full text content of the message.
        token_count (int | None): Approximate token count for this message.
        created_at (datetime): Timestamp when the message was created.
    """

    __tablename__ = "messages"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_id = Column(BigInteger, nullable=True)  # BIGSERIAL in PostgreSQL; NULL in SQLite tests
    conversation_id = Column(Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Alarm(Base):
    """Audit record for a flagged (harmful/policy-violating) message.

    Attributes:
        id (uuid.UUID): Primary key.
        message_id (uuid.UUID): Foreign key to the flagged message.
        reason (str): Human-readable description of why the message was flagged.
    """

    __tablename__ = "alarm"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(Uuid(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    reason = Column(Text, nullable=False)
