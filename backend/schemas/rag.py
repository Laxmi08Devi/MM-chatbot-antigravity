"""
Pydantic schemas for RAG query and indexing endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.schemas.chat import Citation


class RAGQueryRequest(BaseModel):
    """Query request for RAG answer generation."""
    query: str = Field(..., min_length=1, description="Question to answer using indexed documents.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to record message.")
    top_k: int = Field(4, ge=1, le=10, description="Maximum number of context chunks to retrieve.")
    similarity_threshold: float = Field(0.20, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff.")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only RAG queries."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return v.strip()


class RAGQueryResponse(BaseModel):
    """Answer with source attribution and citations."""
    answer: str
    sources: List[Citation]
    chunks_used: int
    conversation_id: Optional[str] = None

