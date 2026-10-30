"""
Pydantic schemas for Document Management: creation, listing, updating, and download.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    """Payload to create a new editable text document."""
    title: str = Field(..., min_length=1, max_length=255, description="Document title.")
    content: str = Field(..., min_length=1, description="Text content.")
    file_type: str = Field("txt", description="Document type: txt, md, etc.")


class DocumentUpdateRequest(BaseModel):
    """Payload to update an existing document's title or text."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)


class DocumentResponse(BaseModel):
    """Document metadata and content."""
    id: str
    title: str
    file_type: str
    file_path: Optional[str] = None
    file_size_bytes: int
    content: str
    is_user_created: bool
    chunks_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentSummary(BaseModel):
    """Document summary for list views."""
    id: str
    title: str
    file_type: str
    file_size_bytes: int
    is_user_created: bool
    chunks_count: int = 0
    created_at: datetime
    updated_at: datetime

