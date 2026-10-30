"""
RAG endpoints: querying grounded knowledge and triggering document indexing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.rag import RAGQueryRequest, RAGQueryResponse
from backend.schemas.common import GenericResponse
from backend.services.rag_service import RAGService

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(request: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    Search indexed documents using semantic similarity and generate a grounded answer with citations.
    If conversation_id is provided, automatically records user and assistant messages in conversation history.
    """
    # 1. Answer query using RAGService
    rag_result = RAGService.answer_query(
        db=db,
        query=request.query,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold
    )

    conv_id = request.conversation_id
    if conv_id:
        conv = repository.get_conversation(db, conv_id)
        if not conv:
            conv = repository.create_conversation(db, title=request.query[:40], mode="rag")
            conv_id = conv.id

        # Persist user message
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="user",
            content=request.query,
            message_type="rag"
        )
        # Persist assistant message
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="assistant",
            content=rag_result["answer"],
            message_type="rag",
            sources=rag_result["sources"]
        )

    return RAGQueryResponse(
        answer=rag_result["answer"],
        sources=rag_result["sources"],
        chunks_used=rag_result["chunks_used"],
        conversation_id=conv_id
    )


@router.post("/index/{document_id}", response_model=GenericResponse)
def index_document(document_id: str, db: Session = Depends(get_db)):
    """
    Trigger chunking and embedding generation for a specified document.
    """
    doc = repository.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        count = RAGService.index_document(db, document_id)
        return GenericResponse(
            success=True,
            message=f"Indexed {count} chunks for document '{doc.title}'.",
            data={"document_id": document_id, "chunks_count": count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )

