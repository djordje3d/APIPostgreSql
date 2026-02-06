"""Tickets API integration tests (entry/exit flow)."""
import pytest
from fastapi.testclient import TestClient


def test_list_tickets_returns_paginated(client: TestClient) -> None:
    """GET /tickets returns 200 and paginated structure."""
    response = client.get("/tickets")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_ticket_entry_requires_valid_vehicle(client: TestClient) -> None:
    """POST /tickets/entry returns 400 for invalid vehicle_id."""
    payload = {
        "vehicle_id": 999999,
        "garage_id": 1,
    }
    response = client.post("/tickets/entry", json=payload)
    assert response.status_code == 400


def test_ticket_entry_and_list(
    client: TestClient,
) -> None:
    """Create garage, vehicle type, vehicle; then ticket entry; list tickets includes it."""
    # Create garage
    r_garage = client.post(
        "/garages",
        json={
            "name": "Flow Test Garage",
            "capacity": 10,
            "default_rate": 80.0,
        },
    )
    assert r_garage.status_code == 200
    garage_id = r_garage.json()["id"]

    # Create spot so there is a free spot
    r_spot = client.post(
        "/spots",
        json={
            "garage_id": garage_id,
            "code": "A01",
            "is_rentable": False,
            "is_active": True,
        },
    )
    assert r_spot.status_code == 200

    # Create vehicle type and vehicle
    r_vt = client.post(
        "/vehicle-types", json={"type": "BikeFlowTest", "rate": "20.00"}
    )
    assert r_vt.status_code == 200
    vt_id = r_vt.json()["id"]

    r_vehicle = client.post(
        "/vehicles",
        json={
            "licence_plate": "FLOW-001",
            "vehicle_type_id": vt_id,
            "status": 1,
        },
    )
    assert r_vehicle.status_code == 200
    vehicle_id = r_vehicle.json()["id"]

    # Ticket entry
    r_entry = client.post(
        "/tickets/entry",
        json={
            "vehicle_id": vehicle_id,
            "garage_id": garage_id,
        },
    )
    assert r_entry.status_code == 200
    ticket = r_entry.json()
    assert ticket["ticket_state"] == "OPEN"
    assert ticket["vehicle_id"] == vehicle_id
    assert ticket["garage_id"] == garage_id
    ticket_id = ticket["id"]

    # List tickets filtered by garage
    r_list = client.get("/tickets", params={"garage_id": garage_id})
    assert r_list.status_code == 200
    items = r_list.json()["items"]
    ids = [t["id"] for t in items]
    assert ticket_id in ids
