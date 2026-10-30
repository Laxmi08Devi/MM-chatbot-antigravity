"""
Pydantic schemas for conversational chat requests, responses, and history.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class ChatMessageRequest(BaseModel):
    """Incoming user chat message."""
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID. A new one is created if omitted.")
    message: str = Field(..., min_length=1, description="User's text prompt.")
    mode: str = Field("chat", description="Chat mode: chat, rag, search, emotional.")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only messages."""
        if not v or not v.strip():
            raise ValueError("Chat message cannot be empty or contain only whitespace.")
        return v.strip()


class Citation(BaseModel):
    """Citation metadata for grounded RAG or Web Search results."""
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Outgoing assistant response message."""
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    message_type: str = "text"
    sources: Optional[List[Citation]] = None
    media_url: Optional[str] = None
    created_at: datetime


class MessageItem(BaseModel):
    """Individual message in history."""
    id: str
    role: str
    content: str
    message_type: str
    sources: Optional[List[Dict[str, Any]]] = None
    media_url: Optional[str] = None
    created_at: datetime


class ConversationItem(BaseModel):
    """Conversation summary item."""
    id: str
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    """Conversation summary with full message history."""
    conversation: ConversationItem
    messages: List[MessageItem]

