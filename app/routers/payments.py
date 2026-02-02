from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import SessionLocal
from app import models, schemas
from app.services.payments import recalc_ticket_payment_status

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def create_payment(data: schemas.PaymentCreate, db: Session = Depends(get_db)):

    ticket = db.get(models.Ticket, data.ticket_id)
    if not ticket:
        raise HTTPException(400, "Invalid ticket_id")

    try:

        p = models.Payment(
            ticket_id=data.ticket_id,
            amount=data.amount,
            method=data.method,
            currency=data.currency,
            paid_at=data.paid_at or datetime.utcnow(),
        )
        db.add(p)

        # auto update ticket.payment_status
        # recalculacija statusa (bez commit unutra)
        recalc_ticket_payment_status(db, data.ticket_id)

        # 1 commit za sve
        db.commit()
        db.refresh(p)

        return p

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Payment failed: {str(e)}")


@router.get("/{payment_id}")
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.get("/by-ticket/{ticket_id}")
def payments_by_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Payment)
        .filter(models.Payment.ticket_id == ticket_id)
        .order_by(models.Payment.id)
        .all()
    )
