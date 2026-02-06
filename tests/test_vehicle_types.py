"""Vehicle types API integration tests."""
import pytest
from fastapi.testclient import TestClient


def test_list_vehicle_types_returns_paginated(client: TestClient) -> None:
    """GET /vehicle-types returns 200 and paginated structure."""
    response = client.get("/vehicle-types")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_create_and_get_vehicle_type(client: TestClient) -> None:
    """POST /vehicle-types creates a type; GET /vehicle-types/{id} returns it."""
    payload = {"type": "Car", "rate": "50.00"}
    r = client.post("/vehicle-types", json=payload)
    assert r.status_code == 200
    created = r.json()
    assert created["type"] == payload["type"]
    vt_id = created["id"]

    r2 = client.get(f"/vehicle-types/{vt_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == vt_id
    assert r2.json()["type"] == payload["type"]


def test_get_vehicle_type_404(client: TestClient) -> None:
    """GET /vehicle-types/{id} returns 404 for non-existent id."""
    response = client.get("/vehicle-types/999999")
    assert response.status_code == 404
