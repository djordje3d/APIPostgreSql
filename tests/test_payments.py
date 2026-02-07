"""Payments API integration tests."""

import pytest
from fastapi.testclient import TestClient


def test_create_payment_for_closed_ticket(client: TestClient) -> None:
    """Create garage, spot, vehicle, ticket entry then exit; create payment; list by ticket."""
    # Garage
    r = client.post(
        "/garages",
        json={"name": "Pay Garage", "capacity": 10, "default_rate": "100.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]

    # Spot
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "P01", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200

    # Vehicle type and vehicle
    r = client.post("/vehicle-types", json={"type": "CarPay", "rate": "50.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "PAY-001", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]

    # Entry then exit (API computes fee and CLOSED when USE_API_FEE_CALCULATION=true)
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200
    ticket_id = r.json()["id"]

    r = client.post(f"/tickets/{ticket_id}/exit", json={})
    assert r.status_code == 200
    assert r.json()["ticket_state"] == "CLOSED"

    # Create payment
    r = client.post(
        "/payments",
        json={"ticket_id": ticket_id, "amount": "50.00", "method": "CASH", "currency": "RSD"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ticket_id"] == ticket_id
    assert data["amount"] == "50.00"

    # List payments by ticket
    r = client.get(f"/payments/by-ticket/{ticket_id}")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert any(p["id"] == data["id"] for p in items)


def test_payment_rejected_for_open_ticket(client: TestClient) -> None:
    """Payment only allowed for closed tickets."""
    r = client.post(
        "/garages",
        json={"name": "Pay Garage 2", "capacity": 5, "default_rate": "80.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "P02", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "BikePay", "rate": "20.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "PAY-002", "vehicle_type_id": vt_id, "status": 1},
    )
    assert r.status_code == 200
    vehicle_id = r.json()["id"]
    r = client.post(
        "/tickets/entry",
        json={"vehicle_id": vehicle_id, "garage_id": garage_id},
    )
    assert r.status_code == 200
    ticket_id = r.json()["id"]

    r = client.post(
        "/payments",
        json={"ticket_id": ticket_id, "amount": "10.00", "method": "CARD", "currency": "RSD"},
    )
    assert r.status_code == 400


def test_payment_overpayment_rejected(client: TestClient) -> None:
    """Payment that would exceed ticket fee is rejected."""
    r = client.post(
        "/garages",
        json={"name": "Pay Garage 3", "capacity": 5, "default_rate": "30.00"},
    )
    assert r.status_code == 200
    garage_id = r.json()["id"]
    r = client.post(
        "/spots",
        json={"garage_id": garage_id, "code": "P03", "is_rentable": False, "is_active": True},
    )
    assert r.status_code == 200
    r = client.post("/vehicle-types", json={"type": "MotoPay", "rate": "15.00"})
    assert r.status_code == 200
    vt_id = r.json()["id"]
    r = client.post(
        "/vehicles",
        json={"licence_plate": "PAY-003", "vehicle_type_id": vt_id, "status": 1},
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
    fee = r.json().get("fee")
    # Fee is at least 1 unit (e.g. 15). Overpay by a lot.
    r = client.post(
        "/payments",
        json={"ticket_id": ticket_id, "amount": "99999.00", "method": "CASH", "currency": "RSD"},
    )
    assert r.status_code == 400


def test_get_payment_404(client: TestClient) -> None:
    """GET /payments/{id} returns 404 for non-existent id."""
    r = client.get("/payments/999999")
    assert r.status_code == 404
