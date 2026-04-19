"""Aggregated counts and revenue for GET /dashboard/analytics."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import exists, func
from sqlalchemy.orm import Session, joinedload

from app import models
from app.services.pricing import get_ticket_fee


def compute_spot_ticket_counts(
    db: Session, garage_id: int | None
) -> tuple[int, int, int, int]:
    """Match StatusCards: free, occupied, inactive, open_tickets."""
    base = db.query(models.ParkingSpot)
    if garage_id is not None:
        base = base.filter(models.ParkingSpot.garage_id == garage_id)

    total_all = base.count()
    total_active = base.filter(models.ParkingSpot.is_active.is_(True)).count()

    free_count = base.filter(
        models.ParkingSpot.is_active.is_(True),
        ~exists().where(
            (models.Ticket.spot_id == models.ParkingSpot.id)
            & (models.Ticket.ticket_state == "OPEN"),
        ),
    ).count()

    inactive = max(0, total_all - total_active)
    occupied = max(0, total_active - free_count)

    tq = db.query(models.Ticket).filter(models.Ticket.ticket_state == "OPEN")
    if garage_id is not None:
        tq = tq.filter(models.Ticket.garage_id == garage_id)
    open_tickets = tq.count()

    return free_count, occupied, inactive, open_tickets


def _payment_base_query(db: Session, garage_id: int | None):
    q = db.query(models.Payment)
    if garage_id is not None:
        q = q.join(models.Ticket).filter(models.Ticket.garage_id == garage_id)
    return q


def sum_payments_in_range(
    db: Session,
    garage_id: int | None,
    from_date: date,
    to_date_inclusive: date,
) -> float:
    """Sum payment amounts for paid_at in UTC day range (inclusive end date)."""
    start = datetime.fromisoformat(from_date.isoformat() + "T00:00:00+00:00")
    end_exclusive = datetime.fromisoformat(
        (to_date_inclusive + timedelta(days=1)).isoformat() + "T00:00:00+00:00"
    )
    q = _payment_base_query(db, garage_id).filter(
        models.Payment.paid_at >= start,
        models.Payment.paid_at < end_exclusive,
    )
    total = q.with_entities(
        func.coalesce(func.sum(models.Payment.amount), 0),
    ).scalar()
    return float(total or 0)


def count_unpaid_and_partial(db: Session, garage_id: int | None) -> int:
    q1 = db.query(models.Ticket).filter(
        models.Ticket.payment_status == "UNPAID",
    )
    q2 = db.query(models.Ticket).filter(
        models.Ticket.payment_status == "PARTIALLY_PAID",
    )
    if garage_id is not None:
        q1 = q1.filter(models.Ticket.garage_id == garage_id)
        q2 = q2.filter(models.Ticket.garage_id == garage_id)
    return q1.count() + q2.count()


def compute_total_outstanding(db: Session, garage_id: int | None) -> float:
    """Same logic as GET /payments/outstanding."""
    q = (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.vehicle).joinedload(models.Vehicle.vehicle_type),
        )
        .filter(
            models.Ticket.ticket_state == "CLOSED",
            models.Ticket.payment_status.in_(["UNPAID", "PARTIALLY_PAID"]),
        )
    )
    if garage_id is not None:
        q = q.filter(models.Ticket.garage_id == garage_id)
    tickets = q.all()
    total = 0.0
    for t in tickets:
        if t.entry_time is not None and t.exit_time is not None:
            fee = float(get_ticket_fee(t, db))
        else:
            fee = float(t.fee or 0)
        paid = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.ticket_id == t.id)
            .scalar()
        )
        total += fee - float(paid)
    return max(0.0, total)


def compute_rest_to_pay_for_ticket(
    db: Session, ticket: models.Ticket, paid: Decimal | float
) -> float:
    """Remaining amount for dashboard row (0 when OPEN or PAID)."""
    if ticket.ticket_state == "OPEN" or ticket.payment_status == "PAID":
        return 0.0
    if ticket.entry_time is not None and ticket.exit_time is not None:
        fee = float(get_ticket_fee(ticket, db))
    else:
        fee = float(ticket.fee or 0)
    return max(0.0, fee - float(paid))


def batch_payment_totals_by_ticket(
    db: Session, ticket_ids: list[int]
) -> dict[int, float]:
    if not ticket_ids:
        return {}
    rows = (
        db.query(
            models.Payment.ticket_id,
            func.coalesce(func.sum(models.Payment.amount), 0),
        )
        .filter(models.Payment.ticket_id.in_(ticket_ids))
        .group_by(models.Payment.ticket_id)
        .all()
    )
    return {tid: float(amt) for tid, amt in rows}
