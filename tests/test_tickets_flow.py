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


def test_ticket_exit_success(client: TestClient) -> None:
    """POST /tickets/{id}/exit closes the ticket and sets fee when USE_API_FEE_CALCULATION=true."""
    r = client.post(
        "/garages",
        json={"name": "Exit Garage", "capacity": 5, "default_rate": "25.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "E01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "ExitBike", "rate": "10.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "EXIT-1", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200
    ticket_id = r.json()["id"]
    assert r.json()["ticket_state"] == "OPEN"
    assert r.json()["exit_time"] is None

    r = client.post(f"/tickets/{ticket_id}/exit", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["ticket_state"] == "CLOSED"
    assert data["exit_time"] is not None
    assert data["fee"] is not None


def test_ticket_exit_already_closed_400(client: TestClient) -> None:
    """POST /tickets/{id}/exit returns 400 if ticket is not OPEN."""
    r = client.post(
        "/garages",
        json={"name": "Exit Garage 2", "capacity": 5, "default_rate": "30.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "E02", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "ExitCar", "rate": "15.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "EXIT-2", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200
    ticket_id = r.json()["id"]
    r = client.post(f"/tickets/{ticket_id}/exit", json={})
    assert r.status_code == 200
    r = client.post(f"/tickets/{ticket_id}/exit", json={})
    assert r.status_code == 400


def test_list_tickets_filter_by_state(client: TestClient) -> None:
    """GET /tickets?state=OPEN and state=CLOSED return only matching tickets."""
    r = client.get("/tickets", params={"state": "OPEN"})
    assert r.status_code == 200
    for t in r.json()["items"]:
        assert t["ticket_state"] == "OPEN"

    r = client.get("/tickets", params={"state": "CLOSED"})
    assert r.status_code == 200
    for t in r.json()["items"]:
        assert t["ticket_state"] == "CLOSED"


def test_list_tickets_filter_by_payment_status(client: TestClient) -> None:
    """GET /tickets?payment_status=X returns only matching tickets."""
    r = client.get("/tickets", params={"payment_status": "PAID"})
    assert r.status_code == 200
    for t in r.json()["items"]:
        assert t["payment_status"] == "PAID"

    r = client.get("/tickets", params={"payment_status": "UNPAID"})
    assert r.status_code == 200
    for t in r.json()["items"]:
        assert t["payment_status"] == "UNPAID"


def test_list_tickets_filter_by_garage_id(client: TestClient) -> None:
    """GET /tickets?garage_id=X returns only tickets for that garage."""
    r = client.post(
        "/garages",
        json={"name": "Filter Garage", "capacity": 5, "default_rate": "20.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "F01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "FilterBike", "rate": "5.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "FLT-1", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200
    ticket_id = r.json()["id"]

    r = client.get("/tickets", params={"garage_id": garage_id})
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()["items"]]
    assert ticket_id in ids
    for t in r.json()["items"]:
        assert t["garage_id"] == garage_id


def test_get_ticket_404(client: TestClient) -> None:
    """GET /tickets/{id} returns 404 for non-existent id."""
    r = client.get("/tickets/999999")
    assert r.status_code == 404
