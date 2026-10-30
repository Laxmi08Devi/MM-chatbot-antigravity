"""
Tests for Phase 6: Multimodal image vision, image generation, audio transcription, and TTS.
"""

import io
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_vision_endpoint_upload():
    """Verify vision endpoint accepts image upload and returns analysis."""
    # Create a small valid test image in memory
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    upload_file = ("test_image.png", io.BytesIO(img_bytes), "image/png")
    response = client.post(
        "/api/multimodal/vision",
        files={"file": upload_file},
        data={"prompt": "What color is this square?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "image_url" in data
    assert data["image_url"].startswith("/media/uploads/")


def test_image_generation_notice_without_key():
    """Verify image generation provides clear notice when OpenAI key is not configured."""
    response = client.post(
        "/api/multimodal/generate-image",
        json={"prompt": "A serene mountain lake at sunrise"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    if not data["success"]:
        assert "image generation requires" in data["message"].lower() or "openai" in data["message"].lower()


def test_audio_transcription_endpoint():
    """Verify audio transcription endpoint accepts audio file and returns transcript structure."""
    fake_audio = b"RIFF....WAVEfmt ...."
    upload_file = ("speech.wav", io.BytesIO(fake_audio), "audio/wav")
    response = client.post(
        "/api/audio/transcribe",
        files={"file": upload_file}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert data["filename"] == "speech.wav"


def test_text_to_speech_endpoint():
    """Verify TTS endpoint creates an audio file and returns its URL."""
    response = client.post(
        "/api/audio/tts",
        json={"text": "Hello, welcome to multimodal AI.", "voice": "alloy"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["audio_url"] is not None
    assert data["audio_url"].startswith("/media/generated/")
    assert data["audio_url"].endswith(".mp3")


def test_vision_validation_unsupported_empty_and_oversized():
    """Verify vision endpoint rejects unsupported formats, empty files, and oversized images."""
    # 1. Unsupported extension (.exe / .txt)
    bad_file = ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")
    resp_ext = client.post("/api/multimodal/vision", files={"file": bad_file})
    assert resp_ext.status_code == 400
    assert "not supported" in resp_ext.json()["detail"].lower()

    # 2. Empty file (0 bytes)
    empty_file = ("empty.png", io.BytesIO(b""), "image/png")
    resp_empty = client.post("/api/multimodal/vision", files={"file": empty_file})
    assert resp_empty.status_code == 400
    assert "empty" in resp_empty.json()["detail"].lower()

    # 3. Oversized file (> 10MB)
    huge_bytes = b"0" * (11 * 1024 * 1024)
    huge_file = ("huge.png", io.BytesIO(huge_bytes), "image/png")
    resp_huge = client.post("/api/multimodal/vision", files={"file": huge_file})
    assert resp_huge.status_code == 413
    assert "exceeds maximum allowed size" in resp_huge.json()["detail"].lower()


def test_audio_validation_unsupported_empty_and_oversized():
    """Verify audio transcribe endpoint rejects unsupported formats, empty files, and oversized audio."""
    # 1. Unsupported extension (.pdf)
    bad_file = ("document.pdf", io.BytesIO(b"%PDF-1.4..."), "application/pdf")
    resp_ext = client.post("/api/audio/transcribe", files={"file": bad_file})
    assert resp_ext.status_code == 400
    assert "not supported" in resp_ext.json()["detail"].lower()

    # 2. Empty file (0 bytes)
    empty_file = ("empty.wav", io.BytesIO(b""), "audio/wav")
    resp_empty = client.post("/api/audio/transcribe", files={"file": empty_file})
    assert resp_empty.status_code == 400
    assert "empty" in resp_empty.json()["detail"].lower()

    # 3. Oversized file (> 10MB)
    huge_bytes = b"0" * (11 * 1024 * 1024)
    huge_file = ("huge.mp3", io.BytesIO(huge_bytes), "audio/mpeg")
    resp_huge = client.post("/api/audio/transcribe", files={"file": huge_file})
    assert resp_huge.status_code == 413
    assert "exceeds maximum allowed size" in resp_huge.json()["detail"].lower()


def test_audio_query_endpoint_success_with_mock():
    """Verify audio query endpoint transcribes audio, submits to chatbot, and persists turn."""
    fake_audio = b"RIFF....WAVEfmt ...."
    upload_file = ("question.wav", io.BytesIO(fake_audio), "audio/wav")

    with patch("backend.services.audio_service.AudioService.transcribe_audio", return_value="What is Multimodal AI?"):
        with patch("backend.services.chat_service.ChatService.generate_reply", return_value="Multimodal AI combines text, vision, and audio."):
            response = client.post(
                "/api/audio/query",
                files={"file": upload_file},
                data={"mode": "chat"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["transcript"] == "What is Multimodal AI?"
            assert "combines text, vision, and audio" in data["response"]
            assert "conversation_id" in data
            assert data["filename"] == "question.wav"

            # Check that conversation was persisted in database
            conv_id = data["conversation_id"]
            detail = client.get(f"/api/chat/conversations/{conv_id}").json()
            assert len(detail["messages"]) == 2
            assert detail["messages"][0]["role"] == "user"
            assert detail["messages"][0]["content"] == "What is Multimodal AI?"
            assert detail["messages"][0]["message_type"] == "audio"
            assert detail["messages"][1]["role"] == "assistant"
            assert "combines text, vision, and audio" in detail["messages"][1]["content"]


def test_audio_transcribe_then_chat_flow():
    """Verify end-to-end multi-step flow: transcribe audio first, then submit transcript to chat."""
    fake_audio = b"RIFF....WAVEfmt ...."
    upload_file = ("prompt.wav", io.BytesIO(fake_audio), "audio/wav")

    with patch("backend.services.audio_service.AudioService.transcribe_audio", return_value="How does speech recognition work?"):
        # Step 1: Transcribe audio
        transcribe_resp = client.post("/api/audio/transcribe", files={"file": upload_file})
        assert transcribe_resp.status_code == 200
        transcript = transcribe_resp.json()["transcript"]
        assert transcript == "How does speech recognition work?"

        # Step 2: Submit the transcript to chat endpoint
        chat_resp = client.post(
            "/api/chat/message",
            json={"message": transcript, "mode": "chat"}
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "conversation_id" in chat_data
        assert chat_data["role"] == "assistant"
        assert len(chat_data["content"]) > 0


def test_audio_query_endpoint_transcription_failure():
    """Verify audio query returns 400 error when transcription fails or returns warning."""
    fake_audio = b"RIFF....WAVEfmt ...."
    upload_file = ("bad.wav", io.BytesIO(fake_audio), "audio/wav")

    with patch("backend.services.audio_service.AudioService.transcribe_audio", return_value="⚠️ Audio Transcription Unavailable"):
        response = client.post(
            "/api/audio/query",
            files={"file": upload_file}
        )
        assert response.status_code == 400
        assert "Audio Transcription Unavailable" in response.json()["detail"]

