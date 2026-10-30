"""
Chat service isolating AI model providers (OpenAI, Gemini).
Formats messages, handles context memory, and safely handles provider failures or missing keys.
"""

import logging
from typing import List, Dict, Any, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_DEFAULT = (
    "You are a helpful, versatile, multimodal AI Assistant. "
    "Provide clear, accurate, friendly, and well-structured answers in markdown format."
)


class ChatService:
    """Orchestrates AI text chat generation across configured providers."""

    @classmethod
    def generate_reply(
        cls,
        history: List[Dict[str, str]],
        user_message: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate an AI response given message history and the current user message.
        Falls back cleanly if API keys are not configured.
        """
        sys_prompt = system_instruction or SYSTEM_PROMPT_DEFAULT
        provider = settings.AI_PROVIDER.lower().strip()

        if provider == "openai":
            return cls._generate_openai_reply(history, user_message, sys_prompt)
        elif provider == "gemini":
            return cls._generate_gemini_reply(history, user_message, sys_prompt)
        else:
            return (
                f"Configured AI provider '{provider}' is not supported. "
                f"Please set AI_PROVIDER in .env to 'openai' or 'gemini'."
            )

    @classmethod
    def _generate_openai_reply(
        cls,
        history: List[Dict[str, str]],
        user_message: str,
        system_instruction: str
    ) -> str:
        """Call OpenAI Chat Completions API."""
        if not settings.has_openai:
            return (
                "⚠️ **OpenAI API Key Not Configured**\n\n"
                "To enable live conversational AI with OpenAI, please add your `OPENAI_API_KEY` "
                "to the `.env` file and restart the backend server."
            )

        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Build messages array
            messages = [{"role": "system", "content": system_instruction}]
            for msg in history[-10:]:  # Keep recent context window
                role = "assistant" if msg.get("role") == "assistant" else "user"
                messages.append({"role": role, "content": msg.get("content", "")})
            messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI API call failed: %s", str(e))
            return f"⚠️ **OpenAI Service Notice**: Unable to generate response ({str(e)}). Please verify your API key and connection."

    @classmethod
    def _generate_gemini_reply(
        cls,
        history: List[Dict[str, str]],
        user_message: str,
        system_instruction: str
    ) -> str:
        """Call Google Gemini API."""
        if not settings.has_gemini:
            return (
                "⚠️ **Gemini API Key Not Configured**\n\n"
                "To enable live conversational AI with Gemini, please add your `GEMINI_API_KEY` "
                "to the `.env` file and restart the backend server."
            )

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_instruction
            )

            # Build conversation history
            chat = model.start_chat(history=[])
            for msg in history[-10:]:
                role = "model" if msg.get("role") == "assistant" else "user"
                chat.history.append({"role": role, "parts": [msg.get("content", "")]})

            response = chat.send_message(user_message)
            return response.text or ""
        except Exception as e:
            logger.error("Gemini API call failed: %s", str(e))
            return f"⚠️ **Gemini Service Notice**: Unable to generate response ({str(e)}). Please verify your API key and connection."

