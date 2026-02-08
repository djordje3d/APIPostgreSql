from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date, timedelta

from app.db import get_db
from app import models, schemas
from app.config import USE_API_PAYMENT_STATUS
from app.services.payments import recalc_ticket_payment_status

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.PaymentResponse],
)
def list_payments(
    db: Session = Depends(get_db),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    garage_id: int | None = Query(default=None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List payments, filtered by paid_at date range (inclusive) and garage."""
    q = db.query(models.Payment).order_by(models.Payment.paid_at.desc())
    if garage_id is not None:
        q = q.join(models.Ticket).filter(models.Ticket.garage_id == garage_id)
    if from_date is not None:
        start = datetime.fromisoformat(
            from_date.isoformat() + "T00:00:00+00:00"
        )
        q = q.filter(models.Payment.paid_at >= start)
    if to_date is not None:
        end_exclusive = datetime.fromisoformat(
            (to_date + timedelta(days=1)).isoformat() + "T00:00:00+00:00"
        )
        q = q.filter(models.Payment.paid_at < end_exclusive)
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.post("", response_model=schemas.PaymentResponse)
def create_payment(data: schemas.PaymentCreate, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, data.ticket_id)
    if not ticket:
        raise HTTPException(400, "Invalid ticket_id")

    if ticket.ticket_state != "CLOSED":
        raise HTTPException(400, "Payment only allowed for closed tickets")

    if ticket.fee is not None and ticket.fee > 0:
        total_paid = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.ticket_id == data.ticket_id)
            .scalar()
        )
        if total_paid + data.amount > ticket.fee:
            raise HTTPException(
                400,
                "Payment would exceed ticket fee",
            )

    try:
        p = models.Payment(
            ticket_id=data.ticket_id,
            amount=data.amount,
            method=data.method,
            currency=data.currency,
            paid_at=data.paid_at or datetime.now(timezone.utc),
        )
        db.add(p)
        if USE_API_PAYMENT_STATUS:
            recalc_ticket_payment_status(db, data.ticket_id)
        db.commit()
        db.refresh(p)
        return p
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Payment failed: {str(e)}")


@router.get(
    "/outstanding",
    response_model=schemas.OutstandingResponse,
)
def get_outstanding(
    garage_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Total still to pay for closed UNPAID/PARTIALLY_PAID tickets."""
    q = db.query(models.Ticket).filter(
        models.Ticket.ticket_state == "CLOSED",
        models.Ticket.payment_status.in_(["UNPAID", "PARTIALLY_PAID"]),
    )
    if garage_id is not None:
        q = q.filter(models.Ticket.garage_id == garage_id)
    tickets = q.all()
    total = 0.0
    for t in tickets:
        fee = float(t.fee or 0)
        paid = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.ticket_id == t.id)
            .scalar()
        )
        total += fee - float(paid)
    return schemas.OutstandingResponse(total_outstanding=max(0.0, total))


@router.get(
    "/by-ticket/{ticket_id}",
    response_model=schemas.PaginatedResponse[schemas.PaymentResponse],
)
def payments_by_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = (
        db.query(models.Payment)
        .filter(models.Payment.ticket_id == ticket_id)
        .order_by(models.Payment.id)
    )
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{payment_id}", response_model=schemas.PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.put("/{payment_id}", response_model=schemas.PaymentResponse)
def update_payment(
    payment_id: int, data: schemas.PaymentUpdate, db: Session = Depends(get_db)
):
    """Full replace of a payment by ID. Use PUT for updates (not POST)."""
    p = db.get(models.Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    p.amount = data.amount
    p.method = data.method
    p.currency = data.currency
    p.paid_at = data.paid_at or datetime.now(timezone.utc)
    if USE_API_PAYMENT_STATUS:
        recalc_ticket_payment_status(db, p.ticket_id)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    ticket_id = p.ticket_id
    db.delete(p)
    if USE_API_PAYMENT_STATUS:
        recalc_ticket_payment_status(db, ticket_id)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Cannot delete payment")
