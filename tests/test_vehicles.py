"""Vehicles API integration tests."""

import pytest
from fastapi.testclient import TestClient


def test_list_vehicles_returns_paginated(client: TestClient) -> None:
    """GET /vehicles returns 200 and paginated structure."""
    r = client.get("/vehicles")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_create_vehicle_and_get(client: TestClient) -> None:
    """POST /vehicles creates; GET /vehicles/{id} returns it."""
    r = client.post("/vehicle-types", json={"type": "CarV", "rate": "45.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "VH-001", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["licence_plate"] == "VH-001"
    assert data["vehicle_type_id"] == vt_id
    vehicle_id = data["id"]

    r = client.get(f"/vehicles/{vehicle_id}")
    assert r.status_code == 200
    assert r.json()["id"] == vehicle_id
    assert r.json()["licence_plate"] == "VH-001"


def test_get_vehicle_by_plate(client: TestClient) -> None:
    """GET /vehicles/by-plate/{plate} returns the vehicle."""
    r = client.post("/vehicle-types", json={"type": "BikeV", "rate": "10.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "PLATE-XY", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200

    r = client.get("/vehicles/by-plate/PLATE-XY")
    assert r.status_code == 200
    assert r.json()["licence_plate"] == "PLATE-XY"


def test_get_vehicle_by_plate_404(client: TestClient) -> None:
    """GET /vehicles/by-plate/{plate} returns 404 for unknown plate."""
    r = client.get("/vehicles/by-plate/NONEXISTENT")
    assert r.status_code == 404


def test_get_vehicle_404(client: TestClient) -> None:
    """GET /vehicles/{id} returns 404 for non-existent id."""
    r = client.get("/vehicles/999999")
    assert r.status_code == 404


def test_patch_vehicle(client: TestClient) -> None:
    """PATCH /vehicles/{id} updates only provided fields."""
    r = client.post("/vehicle-types", json={"type": "TruckV", "rate": "80.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "VH-PAT1", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]

    r = client.patch(
        f"/vehicles/{vehicle_id}",
        json={"licence_plate": "VH-PAT2", "status": 2},
    )
    assert r.status_code == 200
    assert r.json()["licence_plate"] == "VH-PAT2"
    assert r.json()["status"] == 2

    r = client.get(f"/vehicles/{vehicle_id}")
    assert r.status_code == 200
    assert r.json()["licence_plate"] == "VH-PAT2"


def test_delete_vehicle_with_tickets_400(client: TestClient) -> None:
    """DELETE /vehicles/{id} returns 400 when vehicle has tickets."""
    r = client.post(
        "/garages",
        json={"name": "Del Garage", "capacity": 5, "default_rate": "20.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "D01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "DelCar", "rate": "10.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "DEL-001", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200

    r = client.delete(f"/vehicles/{vehicle_id}")
    assert r.status_code == 400
