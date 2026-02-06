from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/payments", tags=["Payments"])


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

        db.commit()
        db.refresh(p)

        return p

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Payment failed: {str(e)}")


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
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    db.delete(p)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Cannot delete: payment has tickets")
