"""
Pydantic schemas for Emotional Assistance mode.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EmotionalSupportRequest(BaseModel):
    """Request for personal emotional assistance."""
    message: str = Field(..., min_length=1, description="User's emotional expression or journal reflection.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID.")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only expressions."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return v.strip()


class EmotionalSupportResponse(BaseModel):
    """Supportive AI response with safety flag."""
    response: str
    is_crisis: bool = False
    conversation_id: Optional[str] = None

