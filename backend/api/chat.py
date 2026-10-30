"""
Chat endpoints for messaging, conversation history, and conversation session management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationItem,
    ConversationDetailResponse,
    MessageItem
)
from backend.schemas.common import GenericResponse
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(request: ChatMessageRequest, db: Session = Depends(get_db)):
    """
    Send a message in a conversation. Creates a conversation session if one does not exist.
    Persists user message and assistant reply to database.
    """
    # 1. Get or create conversation
    if request.conversation_id:
        conversation = repository.get_conversation(db, request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {request.conversation_id} not found."
            )
    else:
        # Generate initial title from first few words of message
        title = (request.message[:40] + "...") if len(request.message) > 40 else request.message
        conversation = repository.create_conversation(db, title=title, mode=request.mode)

    # 2. Persist user message
    repository.add_message(
        db=db,
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        message_type="text"
    )

    # 3. Retrieve prior conversation history for context
    db_messages = repository.get_conversation_messages(db, conversation.id)
    history = [
        {"role": m.role, "content": m.content}
        for m in db_messages[:-1]  # Exclude the message we just added
    ]

    # 4. Generate AI response
    reply_text = ChatService.generate_reply(
        history=history,
        user_message=request.message
    )

    # 5. Persist assistant reply
    assistant_msg = repository.add_message(
        db=db,
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        message_type="text"
    )

    return ChatMessageResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        role="assistant",
        content=assistant_msg.content,
        message_type="text",
        created_at=assistant_msg.created_at
    )


@router.get("/conversations", response_model=List[ConversationItem])
def list_conversations(db: Session = Depends(get_db)):
    """List recent conversation sessions."""
    conversations = repository.list_conversations(db)
    return [
        ConversationItem(
            id=c.id,
            title=c.title,
            mode=c.mode,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_detail(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation metadata and all messages."""
    conversation = repository.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found."
        )

    messages = repository.get_conversation_messages(db, conversation_id)
    return ConversationDetailResponse(
        conversation=ConversationItem(
            id=conversation.id,
            title=conversation.title,
            mode=conversation.mode,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        ),
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                message_type=m.message_type,
                sources=m.sources,
                media_url=m.media_url,
                created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.delete("/conversations/{conversation_id}/messages", response_model=GenericResponse)
def clear_messages(conversation_id: str, db: Session = Depends(get_db)):
    """Clear message history in a conversation without deleting the conversation."""
    conversation = repository.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    count = repository.clear_conversation_messages(db, conversation_id)
    return GenericResponse(
        success=True,
        message=f"Cleared {count} messages from conversation.",
        data={"deleted_count": count}
    )


@router.delete("/conversations/{conversation_id}", response_model=GenericResponse)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation session and all its messages."""
    deleted = repository.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    return GenericResponse(
        success=True,
        message="Conversation deleted successfully."
    )

