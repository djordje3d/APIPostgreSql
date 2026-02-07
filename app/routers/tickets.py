from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.db import get_db
from app import models, schemas
from app.config import USE_API_FEE_CALCULATION
from app.services.spots import allocate_free_spot
from app.services.pricing import get_ticket_fee

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.TicketResponse],
)
def list_tickets(
    db: Session = Depends(get_db),
    state: schemas.TicketState | None = Query(default=None),
    payment_status: schemas.PaymentStatus | None = Query(default=None),
    garage_id: int | None = Query(default=None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.Ticket)

    if state:
        q = q.filter(models.Ticket.ticket_state == state)
    if payment_status:
        q = q.filter(models.Ticket.payment_status == payment_status)
    if garage_id is not None:
        q = q.filter(models.Ticket.garage_id == garage_id)

    q = q.order_by(models.Ticket.id.desc())
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    return t


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int,
    data: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    t = db.get(models.Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    update = data.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(t, key, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    db.delete(t)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Cannot delete: ticket has payments")


@router.post("/entry", response_model=schemas.TicketResponse)
def ticket_entry(data: schemas.TicketEntry, db: Session = Depends(get_db)):
    vehicle = db.get(models.Vehicle, data.vehicle_id)
    if not vehicle:
        raise HTTPException(400, "Invalid vehicle_id")

    try:
        # Ako je ručni spot_id prosleđen -> validiraj da pripada garaži, da je active i da nije zauzet
        spot_id = data.spot_id

        if spot_id is not None:
            spot = db.get(models.ParkingSpot, spot_id)
            if not spot:
                raise HTTPException(400, "Invalid spot_id")
            if spot.garage_id != data.garage_id:
                raise HTTPException(400, "spot_id does not belong to this garage")
            if not spot.is_active:
                raise HTTPException(400, "Spot is not active")

            occupied = (
                db.query(models.Ticket)
                .filter(
                    models.Ticket.spot_id == spot_id,
                    models.Ticket.ticket_state == "OPEN",
                )
                .first()
            )
            if occupied:
                raise HTTPException(409, "Spot is occupied")

        else:
            # Auto dodela spota (slobodan spot u toj garaži)
            spot_id = allocate_free_spot(
                db, data.garage_id, rentable_only=data.rentable_only
            )

        t = models.Ticket(
            vehicle_id=data.vehicle_id,
            entry_time=data.entry_time or datetime.now(timezone.utc),
            ticket_state="OPEN",
            payment_status="NOT_APPLICABLE",
            operational_status="OK",
            garage_id=data.garage_id,
            fee=0,
            spot_id=spot_id,
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return t

    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        # npr. "No free spots available"
        raise HTTPException(409, str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Ticket entry failed: {str(e)}")


@router.post("/{ticket_id}/exit", response_model=schemas.TicketResponse)
def ticket_exit(
    ticket_id: int, data: schemas.TicketExit, db: Session = Depends(get_db)
):
    t = db.get(models.Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")

    if t.ticket_state != "OPEN" or t.exit_time is not None:
        raise HTTPException(400, "Ticket is not open")

    t.exit_time = data.exit_time or datetime.now(timezone.utc)

    if USE_API_FEE_CALCULATION:
        t.fee = get_ticket_fee(t, db)
        t.ticket_state = "CLOSED"

    db.commit()
    db.refresh(t)
    return t
