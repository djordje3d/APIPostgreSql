"""Parking spots API integration tests."""

import pytest
from fastapi.testclient import TestClient


def test_list_spots_returns_paginated(client: TestClient) -> None:
    """GET /spots returns 200 and paginated structure."""
    r = client.get("/spots")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


def test_list_spots_filter_by_garage(client: TestClient) -> None:
    """GET /spots?garage_id=X returns only spots for that garage."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage", "capacity": 20, "default_rate": "50.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    spot_id = r.json()["id"]

    r = client.get("/spots", params={"garage_id": garage_id})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(s["id"] == spot_id and s["garage_id"] == garage_id for s in items)


def test_list_spots_active_only(client: TestClient) -> None:
    """GET /spots?active_only=true excludes inactive spots (default)."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage 2", "capacity": 5, "default_rate": "40.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S02", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    spot_id = r.json()["id"]
    r = client.patch(f"/spots/{spot_id}", json={"is_active": False})
    assert r.status_code == 200

    r = client.get("/spots", params={"garage_id": garage_id, "active_only": True})
    assert r.status_code == 200
    items = r.json()["items"]
    assert not any(s["code"] == "S02" for s in items)

    r = client.get("/spots", params={"garage_id": garage_id, "active_only": False})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(s["code"] == "S02" for s in items)


def test_create_spot_and_get(client: TestClient) -> None:
    """POST /spots creates; GET /spots/{id} returns it."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage 3", "capacity": 10, "default_rate": "60.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S03", "is_rentable": True, "is_active": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["garage_id"] == garage_id
    assert data["code"] == "S03"
    assert data["is_rentable"] is True
    spot_id = data["id"]

    r = client.get(f"/spots/{spot_id}")
    assert r.status_code == 200
    assert r.json()["id"] == spot_id
    assert r.json()["code"] == "S03"


def test_spot_code_unique_per_garage(client: TestClient) -> None:
    """Duplicate code in same garage returns 400."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage 4", "capacity": 5, "default_rate": "70.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S04", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S04", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 400


def test_get_spot_404(client: TestClient) -> None:
    """GET /spots/{id} returns 404 for non-existent id."""
    r = client.get("/spots/999999")
    assert r.status_code == 404


def test_list_spots_only_free(client: TestClient) -> None:
    """GET /spots?only_free=true returns only spots not occupied by an OPEN ticket."""
    r = client.post(
        "/garages",
        json={"name": "Free Spot Garage", "capacity": 5, "default_rate": "30.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "F01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    spot_id = r.json()["id"]
    r = client.post("/vehicle-types", json={"type": "FreeBike", "rate": "5.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "FREE-1", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id, "spot_id": spot_id},
    )
    assert r.status_code == 200

    r = client.get("/spots", params={"garage_id": garage_id, "only_free": True})
    assert r.status_code == 200
    items = r.json()["items"]
    assert not any(s["id"] == spot_id for s in items)

    r = client.get("/spots", params={"garage_id": garage_id, "only_free": False})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(s["id"] == spot_id for s in items)


def test_deactivate_spot(client: TestClient) -> None:
    """DELETE /spots/{id} deactivates the spot (sets is_active=False)."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage 5", "capacity": 5, "default_rate": "80.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S05", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    spot_id = r.json()["id"]

    r = client.delete(f"/spots/{spot_id}")
    assert r.status_code == 200

    r = client.get(f"/spots/{spot_id}")
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_activate_spot(client: TestClient) -> None:
    """PATCH /spots/{id}/activate sets is_active=True after deactivation."""
    r = client.post(
        "/garages",
        json={"name": "Spot Garage 6", "capacity": 5, "default_rate": "90.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "S06", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    spot_id = r.json()["id"]

    r = client.delete(f"/spots/{spot_id}")
    assert r.status_code == 200

    r = client.patch(f"/spots/{spot_id}/activate")
    assert r.status_code == 200
    assert r.json()["is_active"] is True

    r = client.get(f"/spots/{spot_id}")
    assert r.status_code == 200
    assert r.json()["is_active"] is True
