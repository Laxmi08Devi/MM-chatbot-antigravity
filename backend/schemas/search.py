"""
Pydantic schemas for Web Search endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.schemas.chat import Citation


class WebSearchRequest(BaseModel):
    """Request for web-grounded answer."""
    query: str = Field(..., min_length=2, description="Web search query string.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID to record interaction.")
    max_results: int = Field(5, ge=1, le=10, description="Maximum number of search results to retrieve.")


class WebSearchResponse(BaseModel):
    """Response containing answer, sources, and conversation ID."""
    answer: str
    sources: List[Citation]
    results_count: int
    conversation_id: Optional[str] = None

