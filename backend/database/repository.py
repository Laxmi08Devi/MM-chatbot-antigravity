"""
Repository layer providing clean CRUD operations for Conversations, Messages, Documents, and Chunks.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import Conversation, Message, Document, DocumentChunk


# --- Conversation Operations ---

def create_conversation(db: Session, title: str = "New Conversation", mode: str = "chat") -> Conversation:
    """Create and persist a new conversation session."""
    conv = Conversation(title=title, mode=mode)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """Retrieve a conversation by its UUID."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def list_conversations(db: Session, limit: int = 50) -> List[Conversation]:
    """List recent conversations."""
    return db.query(Conversation).order_by(desc(Conversation.updated_at)).limit(limit).all()


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """Delete a conversation and all its cascade-related messages."""
    conv = get_conversation(db, conversation_id)
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True


# --- Message Operations ---

def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    message_type: str = "text",
    sources: Optional[list] = None,
    media_url: Optional[str] = None,
    metadata_info: Optional[dict] = None
) -> Message:
    """Add a message to a conversation and touch the conversation's updated_at."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_type=message_type,
        sources=sources,
        media_url=media_url,
        metadata_info=metadata_info
    )
    db.add(msg)
    
    # Update parent conversation's updated_at
    conv = get_conversation(db, conversation_id)
    if conv:
        db.add(conv)
        
    db.commit()
    db.refresh(msg)
    return msg


def get_conversation_messages(db: Session, conversation_id: str) -> List[Message]:
    """Retrieve all messages belonging to a conversation, ordered chronologically."""
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def clear_conversation_messages(db: Session, conversation_id: str) -> int:
    """Clear all messages in a conversation without deleting the conversation container."""
    deleted_count = db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.commit()
    return deleted_count


# --- Document Operations ---

def create_document(
    db: Session,
    title: str,
    content: str,
    file_type: str = "text",
    file_path: Optional[str] = None,
    file_size_bytes: int = 0,
    is_user_created: bool = False
) -> Document:
    """Create and persist a new document."""
    doc = Document(
        title=title,
        content=content,
        file_type=file_type,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        is_user_created=is_user_created
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: str) -> Optional[Document]:
    """Retrieve a document by its ID."""
    return db.query(Document).filter(Document.id == document_id).first()


def list_documents(db: Session, limit: int = 100) -> List[Document]:
    """List stored documents ordered by creation/update."""
    return db.query(Document).order_by(desc(Document.updated_at)).limit(limit).all()


def update_document(
    db: Session,
    document_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None
) -> Optional[Document]:
    """
    Update document metadata and/or content.
    Automatically removes old chunks so stale embeddings are invalidated.
    """
    doc = get_document(db, document_id)
    if not doc:
        return None
        
    if title is not None:
        doc.title = title
    if content is not None:
        doc.content = content
        doc.file_size_bytes = len(content.encode("utf-8"))
        # Invalidate existing chunks so RAG doesn't serve stale content
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: str) -> bool:
    """Delete a document and all associated chunks."""
    doc = get_document(db, document_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


# --- Document Chunk Operations ---

def store_document_chunks(
    db: Session,
    document_id: str,
    chunks_data: List[Tuple[int, str, List[float], int]]
) -> List[DocumentChunk]:
    """
    Store a batch of chunks and their embedding vectors for a document.
    chunks_data: List of (chunk_index, content, embedding_vector, token_count)
    """
    # First remove any prior chunks for this document
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

    created_chunks = []
    for chunk_index, chunk_text, embedding, tokens in chunks_data:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=chunk_text,
            embedding=embedding,
            token_count=tokens
        )
        db.add(chunk)
        created_chunks.append(chunk)

    db.commit()
    return created_chunks


def get_all_chunks(db: Session) -> List[DocumentChunk]:
    """Retrieve all chunks across all documents for retrieval search."""
    return db.query(DocumentChunk).all()


def count_document_chunks(db: Session, document_id: str) -> int:
    """Count chunks indexed for a specific document."""
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()

