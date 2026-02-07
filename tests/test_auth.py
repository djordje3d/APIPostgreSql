"""API key authentication tests.

When API_KEY is set (here via monkeypatch on app.auth.API_KEY), all endpoints
except GET /health must receive header X-API-Key with the same value; otherwise
the API returns 401. When API_KEY is not set, no auth is required.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_key_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable API key auth by patching the value used by the middleware."""
    monkeypatch.setattr("app.auth.API_KEY", "test-secret-key")


def test_protected_endpoint_returns_401_without_api_key(
    client: TestClient, api_key_enabled: None
) -> None:
    """Without X-API-Key header, protected endpoint returns 401 when API_KEY is set."""
    response = client.get("/garages")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "API key" in data["detail"].lower() or "X-API-Key" in data["detail"]


def test_protected_endpoint_returns_401_with_wrong_api_key(
    client: TestClient, api_key_enabled: None
) -> None:
    """With a wrong X-API-Key value, a protected endpoint returns 401."""
    response = client.get("/garages", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_protected_endpoint_returns_200_with_valid_api_key(
    client: TestClient, api_key_enabled: None
) -> None:
    """With the correct X-API-Key header, a protected endpoint returns 200."""
    response = client.get("/garages", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data


def test_health_allowed_without_api_key_when_auth_enabled(
    client: TestClient, api_key_enabled: None
) -> None:
    """GET /health returns 200 without any API key even when API_KEY is set."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_protected_endpoint_accepts_lowercase_header(
    client: TestClient, api_key_enabled: None
) -> None:
    """x-api-key header (lowercase) is accepted like X-API-Key."""
    response = client.get("/garages", headers={"x-api-key": "test-secret-key"})
    assert response.status_code == 200
