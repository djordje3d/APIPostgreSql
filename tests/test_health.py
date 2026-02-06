"""Health endpoint tests."""

import pytest
from fastapi.testclient import TestClient


# test if the health endpoint returns 200 and indicates DB is connected when database is available
def test_health_returns_200_when_db_ok(client: TestClient) -> None:
    """GET /health returns 200 and indicates DB is connected when database is available."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data.get("database") == "connected"


# test if the health endpoint returns JSON with status field
# test if the health endpoint returns JSON with database field
def test_health_returns_json(client: TestClient) -> None:
    """Health response is JSON with status field."""
    response = client.get("/health")
    assert response.headers["content-type"].startswith("application/json")
    assert "status" in response.json()
