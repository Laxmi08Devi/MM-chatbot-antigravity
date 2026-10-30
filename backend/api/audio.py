"""
Audio API endpoints: speech-to-text transcription and text-to-speech synthesis.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.multimodal import (
    AudioTranscriptionResponse,
    AudioQueryResponse,
    TTSRequest,
    TTSResponse
)
from backend.services.audio_service import AudioService, ALLOWED_AUDIO_EXTENSIONS
from backend.services.chat_service import ChatService
from backend.services.document_service import sanitize_filename

router = APIRouter(prefix="/api/audio", tags=["Audio"])


@router.post("/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio (spoken questions, voice notes) into text using Whisper.
    Validates file format and size before processing.
    """
    raw_filename = file.filename or "recording.wav"
    ext = Path(raw_filename).suffix.lower()

    # 1. Reject unsupported audio formats immediately
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed audio formats: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
        )

    # 2. Read bytes and enforce size limits
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    safe_filename = sanitize_filename(raw_filename)
    transcript = AudioService.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=safe_filename
    )

    return AudioTranscriptionResponse(
        transcript=transcript,
        filename=safe_filename
    )


@router.post("/query", response_model=AudioQueryResponse)
async def query_with_audio(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    mode: str = Form("chat"),
    db: Session = Depends(get_db)
):
    """
    End-to-end audio query: transcribes audio, submits text to the chatbot backend,
    and returns both the transcript and the chatbot's AI response.
    """
    raw_filename = file.filename or "recording.wav"
    ext = Path(raw_filename).suffix.lower()

    # 1. Reject unsupported audio formats immediately
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed audio formats: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
        )

    # 2. Read bytes and enforce size limits
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    safe_filename = sanitize_filename(raw_filename)
    transcript = AudioService.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=safe_filename
    )

    # 3. Verify transcription produced meaningful text (not error or warning)
    if not transcript or not transcript.strip() or transcript.strip().startswith("⚠️"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=transcript or "Audio transcription failed to produce any text."
        )

    clean_transcript = transcript.strip()

    # 4. Get or create conversation session
    if conversation_id:
        conv = repository.get_conversation(db, conversation_id)
        if not conv:
            conv = repository.create_conversation(db, title=clean_transcript[:40], mode=mode)
    else:
        conv = repository.create_conversation(db, title=clean_transcript[:40], mode=mode)

    # 5. Persist user message
    repository.add_message(
        db=db,
        conversation_id=conv.id,
        role="user",
        content=clean_transcript,
        message_type="audio"
    )

    # 6. Retrieve conversation history for context
    db_messages = repository.get_conversation_messages(db, conv.id)
    history = [
        {"role": m.role, "content": m.content}
        for m in db_messages[:-1]
    ]

    # 7. Generate assistant reply
    reply_text = ChatService.generate_reply(
        history=history,
        user_message=clean_transcript
    )

    # 8. Persist assistant reply
    repository.add_message(
        db=db,
        conversation_id=conv.id,
        role="assistant",
        content=reply_text,
        message_type="text"
    )

    return AudioQueryResponse(
        transcript=clean_transcript,
        response=reply_text,
        conversation_id=conv.id,
        filename=safe_filename
    )


@router.post("/tts", response_model=TTSResponse)
def text_to_speech(request: TTSRequest):
    """
    Synthesize audio speech from text. Returns URL to the audio file.
    """
    result = AudioService.generate_speech(
        text=request.text,
        voice=request.voice
    )

    return TTSResponse(
        success=result["success"],
        audio_url=result.get("audio_url"),
        provider=result.get("provider"),
        message=result["message"]
    )

