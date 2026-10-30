"""
Audio service: speech-to-text transcription (OpenAI Whisper) and
text-to-speech generation (OpenAI TTS with gTTS fallback).
"""

import io
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, Any

from backend.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}


class AudioService:
    """Manages audio transcription and speech synthesis."""

    @classmethod
    def transcribe_audio(cls, audio_bytes: bytes, filename: str) -> str:
        """
        Transcribe spoken audio into text using OpenAI Whisper API.
        """
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            return f"⚠️ Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"

        if not settings.has_openai:
            return (
                "⚠️ **Audio Transcription Unavailable**: Speech-to-text transcription requires an OpenAI API key. "
                "Please configure `OPENAI_API_KEY` in `.env` to transcribe spoken audio."
            )

        temp_path = None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Write temporary audio file for Whisper API
            gen_dir = settings.get_generated_media_path()
            temp_filename = f"temp_stt_{uuid.uuid4().hex[:8]}{ext}"
            temp_path = gen_dir / temp_filename

            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=settings.OPENAI_WHISPER_MODEL,
                    file=audio_file
                )
            return transcript.text or ""
        except Exception as e:
            logger.error("Whisper transcription error: %s", str(e))
            return f"⚠️ **Audio Transcription Failed**: {str(e)}"
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    @classmethod
    def generate_speech(cls, text: str, voice: str = "alloy") -> Dict[str, Any]:
        """
        Synthesize spoken audio from text.
        Prefers OpenAI TTS-1; falls back to gTTS if OpenAI is unconfigured.
        """
        clean_text = text.strip()
        if not clean_text:
            return {"success": False, "audio_url": None, "message": "Text is empty."}

        gen_dir = settings.get_generated_media_path()
        filename = f"speech_{uuid.uuid4().hex[:10]}.mp3"
        output_path = gen_dir / filename

        # 1. Try OpenAI TTS if configured
        if settings.has_openai:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.audio.speech.create(
                    model=settings.OPENAI_TTS_MODEL,
                    voice=voice,
                    input=clean_text[:4000]
                )
                response.stream_to_file(str(output_path))
                return {
                    "success": True,
                    "audio_url": f"/media/generated/{filename}",
                    "provider": "OpenAI TTS",
                    "message": "Speech generated with OpenAI TTS."
                }
            except Exception as e:
                logger.warning("OpenAI TTS error: %s. Attempting gTTS fallback.", str(e))

        # 2. Fallback to gTTS (zero-cost speech synthesis)
        try:
            from gtts import gTTS
            tts = gTTS(text=clean_text[:1000], lang="en")
            tts.save(str(output_path))
            return {
                "success": True,
                "audio_url": f"/media/generated/{filename}",
                "provider": "gTTS (Local Fallback)",
                "message": "Speech generated with standard speech synthesis."
            }
        except Exception as e:
            logger.error("Speech synthesis failed: %s", str(e))
            return {
                "success": False,
                "audio_url": None,
                "provider": "None",
                "message": f"⚠️ **Speech Generation Failed**: {str(e)}"
            }

