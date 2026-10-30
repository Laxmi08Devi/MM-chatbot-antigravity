"""
Personal Emotional Assistance Service.
Provides empathetic, non-judgmental support, grounding exercises, and journaling prompts
with strict safety boundaries and crisis redirection.
"""

import re
import logging
from typing import Dict, Any, List

from backend.services.chat_service import ChatService

logger = logging.getLogger(__name__)

CRISIS_KEYWORDS = [
    r"\bsuicid",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bhurt myself\b",
    r"\bself[- ]harm\b",
    r"\boverdose\b",
    r"\bno reason to live\b",
    r"\bbetter off dead\b"
]

CRISIS_RESPONSE = (
    "💙 **I care about your safety and well-being.**\n\n"
    "It sounds like you are going through an overwhelming amount of pain right now. "
    "Because I am an AI and not a human or mental health professional, I cannot provide crisis care, "
    "but please know that you are not alone and there is compassionate, free, and confidential support available immediately:\n\n"
    "- **988 Suicide & Crisis Lifeline (USA & Canada):** Call or text **988** (available 24/7, free, confidential)\n"
    "- **Crisis Text Line:** Text **HOME** to **741741**\n"
    "- **International Crisis Lines:** Find support in your country at [findahelpline.com](https://findahelpline.com)\n"
    "- **Emergency Services:** Call your local emergency number (such as 911, 112, or 999) or visit the nearest emergency room.\n\n"
    "Please consider reaching out to a trusted friend, family member, or professional who can be there with you right now."
)

EMOTIONAL_SYSTEM_PROMPT = (
    "You are a compassionate, empathetic, and gentle conversational companion for emotional support.\n\n"
    "CRITICAL GUIDELINES:\n"
    "1. Respond with warmth, active listening, and validation. Validate feelings without judgment.\n"
    "2. You are an AI, NOT a doctor, therapist, or mental health professional. Never diagnose medical or psychiatric conditions, "
    "and never claim to replace human therapy or professional care.\n"
    "3. Do not foster unhealthy emotional dependency or pretend to be a human friend or therapist.\n"
    "4. When appropriate, offer gentle, practical coping mechanisms:\n"
    "   - Grounding exercises (e.g. 5-4-3-2-1 sensory awareness, deep box breathing: 4s inhale, 4s hold, 4s exhale, 4s hold)\n"
    "   - Thoughtful journaling prompts for reflection\n"
    "   - Taking a walk, drinking a glass of water, or speaking with a trusted loved one.\n"
    "5. Keep responses supportive, calming, and concise. Avoid toxic positivity."
)


class EmotionalSupportService:
    """Manages emotional assistance conversations and safety interventions."""

    @classmethod
    def is_crisis_expression(cls, text: str) -> bool:
        """
        Check if message contains expressions of immediate self-harm, suicidal ideation, or extreme crisis.
        Differentiates everyday sadness/burnout from true safety risks.
        """
        normalized = text.lower()
        for pattern in CRISIS_KEYWORDS:
            if re.search(pattern, normalized):
                return True
        return False

    @classmethod
    def respond(
        cls,
        history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """
        Evaluate safety and generate empathetic response.
        """
        # Safety check for immediate danger / self-harm
        if cls.is_crisis_expression(user_message):
            logger.warning("Safety boundary triggered: crisis keywords detected in emotional support request.")
            return {
                "response": CRISIS_RESPONSE,
                "is_crisis": True
            }

        # Everyday emotional support via AI model
        reply = ChatService.generate_reply(
            history=history,
            user_message=user_message,
            system_instruction=EMOTIONAL_SYSTEM_PROMPT
        )

        return {
            "response": reply,
            "is_crisis": False
        }

