import math
from datetime import timedelta, timezone
from decimal import Decimal

from app import models


def _ensure_utc(dt):
    """If datetime is naive, treat as UTC so we can subtract entry from exit safely."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _get_rate_for_ticket(ticket, db) -> Decimal:
    """Resolve hourly rate: vehicle type if present, otherwise garage default_rate."""
    if ticket.vehicle_id and ticket.vehicle and ticket.vehicle.vehicle_type_id:
        vt = ticket.vehicle.vehicle_type
        if vt is not None:
            return Decimal(vt.rate)
    garage = db.get(models.ParkingConfig, ticket.garage_id)
    if garage is not None and garage.default_rate is not None:
        return Decimal(garage.default_rate)
    return Decimal("0")


def calculate_fee(ticket, db) -> Decimal:
    """Fee from entry/exit duration and rate (vehicle type or garage default)."""
    if ticket.entry_time is None or ticket.exit_time is None:
        return Decimal("0")
    entry = _ensure_utc(ticket.entry_time)
    exit_ = _ensure_utc(ticket.exit_time)
    delta: timedelta = exit_ - entry
    minutes = max(1, int(delta.total_seconds() / 60))
    hours = max(1, math.ceil(minutes / 60))
    rate = _get_rate_for_ticket(ticket, db)
    return hours * rate


def get_ticket_fee(ticket, db) -> Decimal:
    """
    Compute fee for a ticket (after exit_time is set).
    Used when USE_API_FEE_CALCULATION is true (no DB trigger).
    """
    return calculate_fee(ticket, db)


# It’s kept for reference, or for future use in an API-based fee calculation.
