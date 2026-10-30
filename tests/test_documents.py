"""
Tests for Phase 5: Document creation, file upload, updating, re-indexing, downloading, and deletion.
"""

import io
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_and_get_document():
    """Verify creating a text document saves to database and indexes chunks."""
    payload = {
        "title": "Machine Learning Fundamentals",
        "content": "Supervised learning trains models on labeled datasets. Unsupervised learning finds hidden patterns.",
        "file_type": "txt"
    }
    create_resp = client.post("/api/documents", json=payload)
    assert create_resp.status_code == 201
    doc = create_resp.json()
    assert doc["title"] == payload["title"]
    assert doc["is_user_created"] is True
    assert doc["chunks_count"] >= 1
    doc_id = doc["id"]

    # Verify retrieval
    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == doc_id


def test_update_document_refreshes_chunks():
    """Verify updating document updates content and regenerates RAG chunks."""
    # 1. Create document
    create_resp = client.post(
        "/api/documents",
        json={"title": "Draft Doc", "content": "Initial short draft content."}
    )
    doc_id = create_resp.json()["id"]

    # 2. Update document
    update_payload = {
        "title": "Finalized Doc",
        "content": "Completely updated content with new facts about Python FastAPI and Streamlit architectures."
    }
    update_resp = client.put(f"/api/documents/{doc_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_doc = update_resp.json()
    assert updated_doc["title"] == "Finalized Doc"
    assert "FastAPI" in updated_doc["content"]
    assert updated_doc["chunks_count"] >= 1


def test_upload_and_download_document():
    """Verify uploading a text file and downloading it."""
    file_bytes = b"Hello from uploaded file. Testing document upload and text extraction pipeline."
    upload_file = ("sample_notes.txt", io.BytesIO(file_bytes), "text/plain")

    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": upload_file}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # Test download
    dl_resp = client.get(f"/api/documents/{doc_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.content == file_bytes


def test_delete_document():
    """Verify deleting a document removes it from database and cascades to chunks."""
    create_resp = client.post(
        "/api/documents",
        json={"title": "Temporary Doc", "content": "Will be deleted."}
    )
    doc_id = create_resp.json()["id"]

    # Delete
    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Check 404
    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404

