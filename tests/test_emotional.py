"""
Tests for Phase 7: Emotional Support mode, safety filters, and crisis hotline interventions.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.emotional_support_service import EmotionalSupportService

client = TestClient(app)


def test_emotional_crisis_detection_heuristic():
    """Verify safety heuristic flags self-harm but does not flag ordinary stress."""
    # Ordinary stress/sadness
    assert not EmotionalSupportService.is_crisis_expression("I had a really tough day at work and feel exhausted.")
    assert not EmotionalSupportService.is_crisis_expression("I feel down today because it is raining.")

    # High-risk crisis statements
    assert EmotionalSupportService.is_crisis_expression("I want to kill myself.")
    assert EmotionalSupportService.is_crisis_expression("I want to end my life.")
    assert EmotionalSupportService.is_crisis_expression("I am thinking about suicide.")


def test_emotional_crisis_intervention_endpoint():
    """Verify crisis expression returns 988 lifeline and safety resources."""
    response = client.post(
        "/api/emotional/respond",
        json={"message": "I feel like I want to die."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis"] is True
    assert "988" in data["response"]
    assert "741741" in data["response"]
    assert "mental health professional" in data["response"].lower()


def test_everyday_emotional_support_endpoint():
    """Verify everyday stress receives supportive reply without triggering false crisis."""
    response = client.post(
        "/api/emotional/respond",
        json={"message": "I am feeling a little overwhelmed by my exams this week."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis"] is False
    assert len(data["response"]) > 0

