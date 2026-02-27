"""API key and JWT token authentication tests.

When API_KEY is set, protected endpoints accept either X-API-Key or Authorization: Bearer <jwt>.
GET /, GET /health, and POST /auth/login are always public.
"""

import pytest
from fastapi.testclient import TestClient

from app.auth_jwt import create_token


@pytest.fixture
def api_key_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable API key auth by patching the value used by the middleware."""
    monkeypatch.setattr("app.auth.API_KEY", "test-secret-key")


def test_protected_endpoint_returns_401_without_api_key(
    client: TestClient, api_key_enabled: None
) -> None:
    """Without X-API-Key or Bearer token, protected endpoint returns 401 when API_KEY is set."""
    response = client.get("/garages")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "authentication" in data["detail"].lower() or "api key" in data["detail"].lower()


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


def test_protected_endpoint_returns_200_with_valid_bearer_token(
    client: TestClient, api_key_enabled: None
) -> None:
    """With a valid JWT in Authorization: Bearer, a protected endpoint returns 200."""
    token = create_token("testuser")
    response = client.get("/garages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and "total" in data


def test_protected_endpoint_returns_401_with_expired_token(
    client: TestClient, api_key_enabled: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With an expired JWT (exp in the past), a protected endpoint returns 401."""
    monkeypatch.setattr("app.auth_jwt.JWT_EXPIRE_MINUTES", -1)  # expire = now - 1 minute
    token = create_token("testuser")
    response = client.get("/garages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "detail" in response.json()


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


# --- Login (POST /auth/login) ---


@pytest.fixture
def login_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env-based login credentials used by the auth router."""
    monkeypatch.setattr("app.routers.auth.AUTH_USERNAME", "testuser")
    monkeypatch.setattr("app.routers.auth.AUTH_PASSWORD", "testpass")


def test_login_returns_200_and_token_when_credentials_match(
    client: TestClient, login_configured: None
) -> None:
    """POST /auth/login with correct username/password returns 200 and access_token."""
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("token_type") == "bearer"
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data.get("expires_in") is not None


def test_login_returns_401_when_wrong_credentials(
    client: TestClient, login_configured: None
) -> None:
    """POST /auth/login with wrong password returns 401."""
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_returns_401_when_unknown_user(
    client: TestClient, login_configured: None
) -> None:
    """POST /auth/login with unknown username returns 401."""
    response = client.post(
        "/auth/login",
        json={"username": "other", "password": "testpass"},
    )
    assert response.status_code == 401


def test_login_returns_503_when_not_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /auth/login when AUTH_USERNAME is not set returns 503."""
    monkeypatch.setattr("app.routers.auth.AUTH_USERNAME", None)
    response = client.post(
        "/auth/login",
        json={"username": "u", "password": "p"},
    )
    assert response.status_code == 503
    assert "detail" in response.json()


# --- GET /auth/me ---


def test_auth_me_returns_200_with_valid_bearer_token(
    client: TestClient, api_key_enabled: None
) -> None:
    """GET /auth/me with valid JWT returns 200 and { sub: username }."""
    token = create_token("testuser")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"sub": "testuser"}


def test_auth_me_returns_401_without_token(
    client: TestClient, api_key_enabled: None
) -> None:
    """GET /auth/me without Bearer token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_401_with_expired_token(
    client: TestClient, api_key_enabled: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /auth/me with expired JWT returns 401."""
    monkeypatch.setattr("app.auth_jwt.JWT_EXPIRE_MINUTES", -1)  # expire = now - 1 minute
    token = create_token("testuser")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


# --- POST /auth/refresh ---


def test_auth_refresh_returns_200_and_new_token(
    client: TestClient, api_key_enabled: None
) -> None:
    """POST /auth/refresh with valid JWT returns 200 and new access_token."""
    token = create_token("testuser")
    response = client.post("/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("token_type") == "bearer"
    assert "access_token" in data
    assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0
    assert data.get("expires_in") is not None


def test_auth_refresh_returns_401_without_token(
    client: TestClient, api_key_enabled: None
) -> None:
    """POST /auth/refresh without Bearer token returns 401."""
    response = client.post("/auth/refresh")
    assert response.status_code == 401
