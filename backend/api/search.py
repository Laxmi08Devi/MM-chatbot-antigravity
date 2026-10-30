"""
Web search API router: queries the web and returns grounded answers with citations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.search import WebSearchRequest, WebSearchResponse
from backend.services.web_search_service import WebSearchService

router = APIRouter(prefix="/api/search", tags=["Web Search"])


@router.post("/query", response_model=WebSearchResponse)
def execute_web_search(request: WebSearchRequest, db: Session = Depends(get_db)):
    """
    Search the web for up-to-date information and return a grounded answer with source links.
    Optionally saves the query and answer in conversation history.
    """
    result = WebSearchService.answer_with_search(
        query=request.query,
        max_results=request.max_results
    )

    conv_id = request.conversation_id
    if conv_id:
        conv = repository.get_conversation(db, conv_id)
        if not conv:
            conv = repository.create_conversation(db, title=request.query[:40], mode="search")
            conv_id = conv.id

        # Record user query
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="user",
            content=request.query,
            message_type="search"
        )
        # Record assistant reply with citations
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="assistant",
            content=result["answer"],
            message_type="search",
            sources=result["sources"]
        )

    return WebSearchResponse(
        answer=result["answer"],
        sources=result["sources"],
        results_count=result["results_count"],
        conversation_id=conv_id
    )

