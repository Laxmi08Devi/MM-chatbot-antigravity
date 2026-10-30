"""
Pydantic schemas for vision, image generation, audio transcription, and TTS.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VisionResponse(BaseModel):
    """Vision analysis response."""
    analysis: str
    image_url: Optional[str] = None
    conversation_id: Optional[str] = None


class ImageGenerationRequest(BaseModel):
    """Request payload for text-to-image generation."""
    prompt: str = Field(..., min_length=2, description="Text prompt describing image to generate.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID.")


class ImageGenerationResponse(BaseModel):
    """Image generation result."""
    success: bool
    media_url: Optional[str] = None
    message: str
    conversation_id: Optional[str] = None


class AudioTranscriptionResponse(BaseModel):
    """Result of speech-to-text audio transcription."""
    transcript: str
    filename: str


class AudioQueryResponse(BaseModel):
    """Result of audio-based query: transcript, AI response, and conversation ID."""
    transcript: str
    response: str
    conversation_id: str
    filename: str


class TTSRequest(BaseModel):
    """Request payload for text-to-speech generation."""
    text: str = Field(..., min_length=1, max_length=4000, description="Text to speak.")
    voice: str = Field("alloy", description="Voice profile: alloy, echo, fable, onyx, nova, shimmer.")


class TTSResponse(BaseModel):
    """Result of speech synthesis."""
    success: bool
    audio_url: Optional[str] = None
    provider: Optional[str] = None
    message: str

