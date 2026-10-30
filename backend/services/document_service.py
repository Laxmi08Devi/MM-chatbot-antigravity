"""
Document service managing lifecycle: creation, file upload, text extraction,
editing, downloading, deleting, and RAG re-indexing.
"""

import os
import re
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database import repository
from backend.database.models import Document
from backend.services.extractor import DocumentExtractor
from backend.services.rag_service import RAGService

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell exploits."""
    clean = Path(filename).name
    # Keep alphanumeric, periods, dashes, underscores
    clean = re.sub(r"[^\w\s\.-]", "_", clean)
    return clean.strip() or f"doc_{uuid.uuid4().hex[:8]}"


class DocumentService:
    """Handles document persistence, text extraction, and automatic RAG synchronization."""

    @classmethod
    def create_text_document(
        cls,
        db: Session,
        title: str,
        content: str,
        file_type: str = "txt"
    ) -> Document:
        """Create a user-authored text document and immediately index it for RAG."""
        doc = repository.create_document(
            db=db,
            title=title,
            content=content,
            file_type=file_type,
            file_path=None,
            file_size_bytes=len(content.encode("utf-8")),
            is_user_created=True
        )
        # Automatically generate RAG chunks
        RAGService.index_document(db, doc.id)
        return doc

    @classmethod
    async def upload_document(cls, db: Session, file: UploadFile) -> Document:
        """
        Validate, save, extract, and index an uploaded document.
        """
        raw_filename = file.filename or "uploaded_file"
        safe_name = sanitize_filename(raw_filename)
        ext = Path(safe_name).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not supported. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Read content and enforce size limits
        content_bytes = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Save to uploads directory
        upload_dir = settings.get_upload_path()
        unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        saved_path = upload_dir / unique_filename

        with open(saved_path, "wb") as f:
            f.write(content_bytes)

        # Extract text
        try:
            extracted_text = DocumentExtractor.extract_text(content_bytes, safe_name)
        except Exception as e:
            # Clean up saved file if extraction completely fails
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract readable text: {str(e)}"
            )

        # Save to database
        doc = repository.create_document(
            db=db,
            title=safe_name,
            content=extracted_text,
            file_type=ext.replace(".", ""),
            file_path=str(saved_path),
            file_size_bytes=len(content_bytes),
            is_user_created=False
        )

        # Index for RAG
        try:
            RAGService.index_document(db, doc.id)
        except Exception:
            pass  # Indexing can be retried if provider key was missing

        return doc

    @classmethod
    def update_document(
        cls,
        db: Session,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Document:
        """
        Update an existing document and automatically refresh its RAG index.
        Invalidates stale chunks and re-indexes.
        """
        doc = repository.update_document(db, document_id, title=title, content=content)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Automatically re-index if content was modified
        if content is not None:
            RAGService.index_document(db, document_id)

        return doc

    @classmethod
    def delete_document(cls, db: Session, document_id: str) -> bool:
        """
        Delete document record, cascade-delete chunks, and clean up physical file.
        """
        doc = repository.get_document(db, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete physical file if present
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass

        return repository.delete_document(db, document_id)

    @classmethod
    def get_document_chunks_count(cls, db: Session, document_id: str) -> int:
        """Count active indexed chunks for document."""
        return repository.count_document_chunks(db, document_id)

