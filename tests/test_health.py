"""
Tests for Phase 1: Environment configuration, database initialization, and health check endpoint.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify the /api/health endpoint returns 200 and expected schema keys."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "providers" in data
    assert "storage" in data
    assert "app_name" in data

