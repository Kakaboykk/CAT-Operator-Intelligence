"""
tests/test_api.py

Phase 1 API tests:
  14. FastAPI /health endpoint responds 200
  15. Health response structure is correct
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_has_required_fields():
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "app" in data
    assert "phase" in data
    assert data["phase"] == 1


def test_health_status_is_ok_or_degraded():
    response = client.get("/health")
    data = response.json()
    assert data["status"] in ("ok", "degraded"), (
        f"Unexpected status value: {data['status']}"
    )
