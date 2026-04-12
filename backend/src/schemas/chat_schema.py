"""Pydantic schemas for chat API request and response shapes.

Schemas act as the validation layer between external client requests
and internal application services for the chat feature.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """Schema for creating a new conversation session."""

    provider: str = Field(description="The AI provider to use (groq, gemini, deepseek).")
    model: str = Field(description="The model name — locked for the lifetime of the conversation.")
    title: str = Field(default="New Chat", description="Human-readable title for the conversation.")


class ConversationResponse(BaseModel):
    """Schema returned after successfully creating a conversation."""

    conversation_id: str = Field(description="The UUID of the newly created conversation.")


class ConversationListItemResponse(BaseModel):
    """Schema representing a summary of a conversation for the sidebar list."""

    id: str = Field(description="The UUID of the conversation.")
    title: str = Field(description="The human-readable title.")
    provider: str = Field(description="The AI provider (groq, gemini, deepseek).")
    model: str = Field(description="The locked model name.")
    last_message: str | None = Field(default=None, description="Preview of the most recent message content.")
    created_at: datetime = Field(description="Timestamp of creation.")
    updated_at: datetime = Field(description="Timestamp of the most recent activity in the conversation.")
    message_count: int = Field(default=0, description="Number of persisted messages in the conversation.")


class SendMessageRequest(BaseModel):
    """Schema for sending a message into a conversation."""

    content: str = Field(min_length=1, description="The user's message content.")


class MessageResponse(BaseModel):
    """Schema representing a single message in the conversation history."""

    role: str = Field(description="The speaker role: 'user' or 'assistant'.")
    content: str = Field(description="The full text content of the message.")


class HistoricChatDashboardQuery(BaseModel):
    """Pagination controls for the security historic chat dashboard."""

    limit: int = Field(default=10, ge=1, le=1000, description="Maximum number of histories to return.")
    offset: int = Field(default=0, ge=0, description="Number of histories to skip before returning results.")


class HistoricChatMessageResponse(BaseModel):
    """Schema representing a single persisted message in a historic conversation."""

    id: str = Field(description="The UUID of the persisted message.")
    role: str = Field(description="The speaker role for this message.")
    content: str = Field(description="The full message content.")
    created_at: datetime = Field(description="When this message was created.")


class HistoricChatHistoryItemResponse(BaseModel):
    """Schema representing one conversation transcript in the security dashboard."""

    conversation_id: str = Field(description="The UUID of the conversation.")
    title: str = Field(description="Human-readable conversation title.")
    user_id: str = Field(description="The UUID of the user who owns the conversation.")
    user_email: str = Field(description="The email of the user who owns the conversation.")
    provider: str = Field(description="The AI provider assigned to the conversation.")
    model: str = Field(description="The model assigned to the conversation.")
    created_at: datetime = Field(description="When the conversation was created.")
    last_activity_at: datetime = Field(description="Most recent message timestamp, or the creation time when empty.")
    message_count: int = Field(description="Total number of persisted messages in the conversation.")
    messages: list[HistoricChatMessageResponse] = Field(
        default_factory=list,
        description="All persisted messages in chronological order.",
    )


class HistoricChatDashboardSummaryResponse(BaseModel):
    """Summary cards displayed above the historic chat dashboard."""

    total_histories: int = Field(description="Total number of conversations persisted in the system.")
    total_messages: int = Field(description="Total number of persisted chat messages.")
    recent_activity: int = Field(description="Number of messages created in the last 24 hours.")
    unique_users: int = Field(description="Number of unique users with at least one conversation.")


class HistoricChatDashboardResponse(BaseModel):
    """Paginated response payload for the security historic chat dashboard."""

    items: list[HistoricChatHistoryItemResponse] = Field(
        default_factory=list,
        description="Conversation histories ordered by most recent activity first.",
    )
    total: int = Field(description="Total number of conversation histories available.")
    limit: int = Field(description="Applied page size.")
    offset: int = Field(description="Applied offset.")
    summary: HistoricChatDashboardSummaryResponse = Field(
        description="Top-line historic chat dashboard statistics.",
    )


class SecurityAlarmEventResponse(BaseModel):
    """Schema representing a persisted moderation alarm event."""

    id: str = Field(description="The UUID of the alarm record.")
    user_id: str = Field(description="The UUID of the user who sent the flagged message.")
    user_email: str = Field(description="The email of the user who sent the flagged message.")
    conversation_id: str = Field(description="The UUID of the conversation that produced the alarm.")
    message_content: str = Field(description="The exact user message content that was flagged.")
    filter_type: str = Field(description="Which moderation layer flagged the content.")
    provider: str = Field(description="The AI provider assigned to the conversation.")
    reason: str | None = Field(default=None, description="Optional human-readable alarm reason.")
    created_at: datetime = Field(description="When the alarm record was created.")
