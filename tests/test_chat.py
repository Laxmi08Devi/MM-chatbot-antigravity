"""
Tests for Phase 2: FastAPI chat endpoints, conversation persistence, and message history.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_send_chat_message_creates_conversation():
    """Verify sending a message creates a conversation and returns assistant reply."""
    response = client.post(
        "/api/chat/message",
        json={"message": "Hello AI!", "mode": "chat"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message_id" in data
    assert data["role"] == "assistant"
    assert len(data["content"]) > 0

    conversation_id = data["conversation_id"]

    # Verify conversation is in the list
    list_resp = client.get("/api/chat/conversations")
    assert list_resp.status_code == 200
    convs = list_resp.json()
    assert any(c["id"] == conversation_id for c in convs)

    # Verify conversation detail contains both user and assistant messages
    detail_resp = client.get(f"/api/chat/conversations/{conversation_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][0]["content"] == "Hello AI!"
    assert detail["messages"][1]["role"] == "assistant"


def test_clear_and_delete_conversation():
    """Verify clearing messages and deleting a conversation."""
    # 1. Create a message
    res = client.post("/api/chat/message", json={"message": "Test message"})
    conv_id = res.json()["conversation_id"]

    # 2. Clear messages
    clear_res = client.delete(f"/api/chat/conversations/{conv_id}/messages")
    assert clear_res.status_code == 200
    assert clear_res.json()["success"] is True

    # 3. Check messages are now 0
    detail = client.get(f"/api/chat/conversations/{conv_id}").json()
    assert len(detail["messages"]) == 0

    # 4. Delete conversation
    del_res = client.delete(f"/api/chat/conversations/{conv_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 5. Verify 404 on deleted conversation
    get_res = client.get(f"/api/chat/conversations/{conv_id}")
    assert get_res.status_code == 404


def test_reject_empty_and_whitespace_chat_messages():
    """Verify empty and whitespace-only messages are rejected with 422 Unprocessable Entity."""
    # 1. Empty string
    empty_resp = client.post("/api/chat/message", json={"message": ""})
    assert empty_resp.status_code == 422

    # 2. Whitespace-only string
    ws_resp = client.post("/api/chat/message", json={"message": "   \n\t  "})
    assert ws_resp.status_code == 422

