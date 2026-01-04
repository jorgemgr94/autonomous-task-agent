"""API endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint should return ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_endpoint():
    """Status endpoint should return agent configuration."""
    response = client.get("/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "agent" in data
    assert "tools" in data
    assert "model" in data["agent"]
    assert "max_iterations" in data["agent"]
    assert "available" in data["tools"]
    assert "count" in data["tools"]


def test_tasks_endpoint_validation():
    """Tasks endpoint should validate request body."""
    # Missing required field
    response = client.post("/tasks", json={})
    assert response.status_code == 422  # Validation error

    # Valid request structure (will call LLM, so we just check it accepts the format)
    # Note: This test requires OPENAI_API_KEY to be set
    # response = client.post("/tasks", json={"task": "What is 2+2?"})
    # assert response.status_code == 200
