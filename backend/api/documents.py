"""
Document management API: create, upload, view, edit, download, and delete documents.
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentSummary
)
from backend.schemas.common import GenericResponse
from backend.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(request: DocumentCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new user-authored text document and immediately index it for RAG.
    """
    doc = DocumentService.create_text_document(
        db=db,
        title=request.title,
        content=request.content,
        file_type=request.file_type
    )
    chunks_count = DocumentService.get_document_chunks_count(db, doc.id)

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_type=doc.file_type,
        file_path=doc.file_path,
        file_size_bytes=doc.file_size_bytes,
        content=doc.content,
        is_user_created=doc.is_user_created,
        chunks_count=chunks_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a document (PDF, TXT, DOCX, MD). Validates file type and size,
    extracts text, stores metadata, and indexes chunks for RAG.
    """
    doc = await DocumentService.upload_document(db=db, file=file)
    chunks_count = DocumentService.get_document_chunks_count(db, doc.id)

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_type=doc.file_type,
        file_path=doc.file_path,
        file_size_bytes=doc.file_size_bytes,
        content=doc.content,
        is_user_created=doc.is_user_created,
        chunks_count=chunks_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.get("", response_model=List[DocumentSummary])
def list_documents(db: Session = Depends(get_db)):
    """
    List all stored documents with metadata and chunk counts.
    """
    docs = repository.list_documents(db)
    results = []
    for d in docs:
        chunks_count = DocumentService.get_document_chunks_count(db, d.id)
        results.append(
            DocumentSummary(
                id=d.id,
                title=d.title,
                file_type=d.file_type,
                file_size_bytes=d.file_size_bytes,
                is_user_created=d.is_user_created,
                chunks_count=chunks_count,
                created_at=d.created_at,
                updated_at=d.updated_at
            )
        )
    return results


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full details and content of a document.
    """
    doc = repository.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_count = DocumentService.get_document_chunks_count(db, doc.id)
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_type=doc.file_type,
        file_path=doc.file_path,
        file_size_bytes=doc.file_size_bytes,
        content=doc.content,
        is_user_created=doc.is_user_created,
        chunks_count=chunks_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update document title or content. Automatically invalidates old embeddings
    and re-indexes new content for RAG.
    """
    doc = DocumentService.update_document(
        db=db,
        document_id=document_id,
        title=request.title,
        content=request.content
    )
    chunks_count = DocumentService.get_document_chunks_count(db, doc.id)

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_type=doc.file_type,
        file_path=doc.file_path,
        file_size_bytes=doc.file_size_bytes,
        content=doc.content,
        is_user_created=doc.is_user_created,
        chunks_count=chunks_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.delete("/{document_id}", response_model=GenericResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document, all associated RAG chunks/embeddings, and physical file on disk.
    """
    deleted = DocumentService.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return GenericResponse(
        success=True,
        message="Document and associated chunks deleted successfully."
    )


@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db)):
    """
    Download document file. If uploaded from file, serves original file;
    if user-created text, serves file with appropriate filename.
    """
    doc = repository.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path and os.path.exists(doc.file_path):
        return FileResponse(
            path=doc.file_path,
            filename=doc.title,
            media_type="application/octet-stream"
        )
    else:
        # User created text document: serve as utf-8 attachment
        safe_title = doc.title if doc.title.endswith(f".{doc.file_type}") else f"{doc.title}.{doc.file_type}"
        return Response(
            content=doc.content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}"'}
        )

