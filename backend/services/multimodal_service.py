"""
Multimodal service: image understanding (vision) and image generation.
Uses live API providers with clear failure and key-missing notifications.
"""

import base64
import io
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

from backend.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class MultimodalService:
    """Handles vision-capable model calls and image generation."""

    @classmethod
    def analyze_image(
        cls,
        image_bytes: bytes,
        filename: str,
        user_prompt: str = "Describe this image in detail and highlight key features."
    ) -> str:
        """
        Analyze image using vision models (OpenAI GPT-4o-mini / Gemini 1.5 Flash).
        """
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return f"⚠️ Unsupported image format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"

        provider = settings.AI_PROVIDER.lower().strip()

        # 1. OpenAI Vision
        if provider == "openai":
            if not settings.has_openai:
                return (
                    "⚠️ **Vision Service Notice**: OpenAI API key is not configured. "
                    "Please set `OPENAI_API_KEY` in `.env` to enable live image understanding."
                )
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)

                mime_type = "image/png" if ext == ".png" else "image/jpeg"
                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                data_url = f"data:{mime_type};base64,{b64_data}"

                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": data_url}}
                            ]
                        }
                    ],
                    max_tokens=800
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.error("OpenAI vision error: %s", str(e))
                return f"⚠️ **Vision Analysis Failed**: {str(e)}"

        # 2. Gemini Vision
        elif provider == "gemini":
            if not settings.has_gemini:
                return (
                    "⚠️ **Vision Service Notice**: Gemini API key is not configured. "
                    "Please set `GEMINI_API_KEY` in `.env` to enable live image understanding."
                )
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(settings.GEMINI_MODEL)
                pil_img = Image.open(io.BytesIO(image_bytes))

                response = model.generate_content([user_prompt, pil_img])
                return response.text or ""
            except Exception as e:
                logger.error("Gemini vision error: %s", str(e))
                return f"⚠️ **Vision Analysis Failed**: {str(e)}"

        return f"Configured AI provider '{provider}' does not support vision in this setup."

    @classmethod
    def generate_image(cls, prompt: str) -> Dict[str, Any]:
        """
        Generate image using OpenAI DALL-E API.
        Saves resulting image file to generated_media directory.
        """
        if not settings.has_openai:
            return {
                "success": False,
                "media_url": None,
                "message": (
                    "⚠️ **Image Generation Unavailable**: DALL-E image generation requires an OpenAI API key. "
                    "Please set `OPENAI_API_KEY` in `.env` to enable this capability."
                )
            }

        try:
            from openai import OpenAI
            import requests

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.images.generate(
                model=settings.OPENAI_IMAGE_MODEL,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            image_url = response.data[0].url
            # Download and persist locally
            img_resp = requests.get(image_url, timeout=30)
            if img_resp.status_code == 200:
                gen_dir = settings.get_generated_media_path()
                filename = f"gen_{uuid.uuid4().hex[:10]}.png"
                file_path = gen_dir / filename
                with open(file_path, "wb") as f:
                    f.write(img_resp.content)

                relative_url = f"/media/generated/{filename}"
                return {
                    "success": True,
                    "media_url": relative_url,
                    "message": f"Successfully generated image for prompt: '{prompt}'"
                }
            else:
                return {
                    "success": False,
                    "media_url": None,
                    "message": "Failed to download generated image from DALL-E service."
                }
        except Exception as e:
            logger.error("Image generation error: %s", str(e))
            return {
                "success": False,
                "media_url": None,
                "message": f"⚠️ **Image Generation Failed**: {str(e)}"
            }

