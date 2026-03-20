"""Pydantic schemas for chat API request and response shapes.

Schemas act as the validation layer between external client requests
and internal application services for the chat feature.
"""
from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """Schema for creating a new conversation session."""

    provider: str = Field(description="The AI provider to use (groq, gemini, deepseek).")
    model: str = Field(description="The model name — locked for the lifetime of the conversation.")
    title: str = Field(default="New Chat", description="Human-readable title for the conversation.")


class ConversationResponse(BaseModel):
    """Schema returned after successfully creating a conversation."""

    conversation_id: str = Field(description="The UUID of the newly created conversation.")


class SendMessageRequest(BaseModel):
    """Schema for sending a message into a conversation."""

    content: str = Field(min_length=1, description="The user's message content.")


class MessageResponse(BaseModel):
    """Schema representing a single message in the conversation history."""

    role: str = Field(description="The speaker role: 'user' or 'assistant'.")
    content: str = Field(description="The full text content of the message.")
