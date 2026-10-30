"""
Health check and system diagnostics endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database.connection import get_db, get_database_info
from backend.schemas.common import HealthResponse

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint returning system status, database connection type,
    pgvector status, and configured external providers.
    """
    db_info = get_database_info()
    
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=db_info,
        providers={
            "openai": settings.has_openai,
            "gemini": settings.has_gemini,
            "tavily": settings.has_tavily,
            "selected_ai_provider": settings.AI_PROVIDER
        },
        storage={
            "upload_dir": str(settings.get_upload_path()),
            "generated_media_dir": str(settings.get_generated_media_path())
        }
    )

