"""
Common Pydantic schemas for health, status, and standard responses.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., json_schema_extra={"example": "ok"})
    app_name: str
    environment: str
    database: Dict[str, Any]
    providers: Dict[str, Any]
    storage: Dict[str, str]


class GenericResponse(BaseModel):
    """Standard message response schema."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
