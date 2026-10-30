"""
SQLAlchemy ORM models for the Multimodal AI Chatbot.
Defines tables for Conversations, Messages, Documents, and Document Chunks.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a unique string UUID."""
    return str(uuid.uuid4())


class Conversation(Base):
    """
    Represents an ongoing or past conversation session.
    """
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, default="New Conversation")
    mode = Column(String(50), nullable=False, default="chat")  # chat, rag, search, emotional
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', mode='{self.mode}')>"


class Message(Base):
    """
    Represents an individual message exchanged within a conversation.
    """
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text")  # 'text', 'image', 'audio', 'rag', 'search', 'emotional'
    
    # Metadata for citations and media
    sources = Column(JSON, nullable=True)  # List of citations: [{ "title": "...", "url": "...", "snippet": "..." }]
    media_url = Column(String(512), nullable=True)  # URL or path to attached/generated media
    metadata_info = Column(JSON, nullable=True)  # Any extra diagnostic or model metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role='{self.role}', type='{self.message_type}')>"


class Document(Base):
    """
    Represents an uploaded or user-created document for RAG and knowledge management.
    """
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, index=True)
    file_type = Column(String(20), nullable=False, default="text")  # 'pdf', 'txt', 'docx', 'md'
    file_path = Column(String(512), nullable=True)  # Local storage path if uploaded from disk
    file_size_bytes = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)  # Full raw or edited document text
    is_user_created = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', type='{self.file_type}')>"


class DocumentChunk(Base):
    """
    Represents a chunked passage of text with its corresponding embedding vector.
    """
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    
    # Embedding stored as a JSON array of floats (e.g., 1536 floats for OpenAI or 768 for Gemini)
    # This works portably across PostgreSQL and SQLite, and allows native pgvector indexing where supported.
    embedding = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_doc_chunk_order", "document_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"

