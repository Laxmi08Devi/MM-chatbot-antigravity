"""
Emotional assistance API: supportive conversational mode with safety guards.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.emotional import EmotionalSupportRequest, EmotionalSupportResponse
from backend.services.emotional_support_service import EmotionalSupportService

router = APIRouter(prefix="/api/emotional", tags=["Emotional Support"])


@router.post("/respond", response_model=EmotionalSupportResponse)
def get_emotional_support(request: EmotionalSupportRequest, db: Session = Depends(get_db)):
    """
    Empathetic emotional support mode. Responds to everyday worries, stress, and reflections.
    Automatically diverts to crisis helpline resources if immediate danger is detected.
    """
    conv_id = request.conversation_id
    if conv_id:
        conv = repository.get_conversation(db, conv_id)
        if not conv:
            conv = repository.create_conversation(db, title=request.message[:40], mode="emotional")
            conv_id = conv.id
    else:
        conv = repository.create_conversation(db, title=request.message[:40], mode="emotional")
        conv_id = conv.id

    # Retrieve prior conversation messages
    db_messages = repository.get_conversation_messages(db, conv_id)
    history = [
        {"role": m.role, "content": m.content}
        for m in db_messages
    ]

    # Save user expression
    repository.add_message(
        db=db,
        conversation_id=conv_id,
        role="user",
        content=request.message,
        message_type="emotional"
    )

    # Process response
    result = EmotionalSupportService.respond(
        history=history,
        user_message=request.message
    )

    # Save assistant response
    repository.add_message(
        db=db,
        conversation_id=conv_id,
        role="assistant",
        content=result["response"],
        message_type="emotional",
        metadata_info={"is_crisis": result["is_crisis"]}
    )

    return EmotionalSupportResponse(
        response=result["response"],
        is_crisis=result["is_crisis"],
        conversation_id=conv_id
    )

