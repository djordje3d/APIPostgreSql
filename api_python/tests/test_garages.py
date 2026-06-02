"""Garages API integration tests."""
import pytest
from fastapi.testclient import TestClient


def test_list_garages_returns_paginated(client: TestClient) -> None:
    """GET /garages returns 200 and a paginated structure."""
    response = client.get("/garages")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_and_get_garage(client: TestClient) -> None:
    """POST /garages creates a garage; GET /garages/{id} returns it."""
    create = {
        "name": "Test Garage",
        "capacity": 50,
        "default_rate": 100.0,
        "lost_ticket_fee": 500.0,
    }
    r = client.post("/garages", json=create)
    assert r.status_code == 200
    created = r.json()
    assert created["name"] == create["name"]
    assert created["capacity"] == create["capacity"]
    garage_id = created["id"]

    r2 = client.get(f"/garages/{garage_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == garage_id
    assert r2.json()["name"] == create["name"]


def test_get_garage_404(client: TestClient) -> None:
    """GET /garages/{id} returns 404 for non-existent id."""
    response = client.get("/garages/999999")
    assert response.status_code == 404
