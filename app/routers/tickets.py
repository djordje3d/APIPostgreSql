from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app import models, schemas
from app.services.pricing import get_ticket_fee
from app.services.tickets import (
    InvalidSpotError,
    InvalidVehicleError,
    NoFreeSpotError,
    SpotGarageMismatchError,
    SpotInactiveError,
    SpotOccupiedError,
    TicketNotFoundError,
    TicketPersistenceError,
    TicketStateError,
    TicketTokenRetryExceededError,
    close_ticket,
    create_ticket_entry,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/dashboard",
    response_model=schemas.PaginatedResponse[schemas.TicketDashboardRow],
)
def list_tickets_dashboard(
    db: Session = Depends(get_db),
    garage_id: int | None = Query(default=None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List tickets with licence_plate and spot_code for dashboard."""
    q = (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.vehicle),
            joinedload(models.Ticket.spot),
            joinedload(models.Ticket.garage),
        )
        .order_by(models.Ticket.id.desc())
    )
    if garage_id is not None:
        q = q.filter(models.Ticket.garage_id == garage_id)
    total = q.count()
    tickets = q.limit(limit).offset(offset).all()
    items = []
    for t in tickets:
        # Use computed fee when entry_time and exit_time are set, so direct DB
        # changes to entry/exit are reflected after refresh (dashboard display only).
        fee = t.fee
        if t.entry_time is not None and t.exit_time is not None:
            fee = get_ticket_fee(t, db)
        items.append(
            schemas.TicketDashboardRow(
                id=t.id,
                entry_time=t.entry_time,
                exit_time=t.exit_time,
                fee=fee,
                ticket_state=t.ticket_state,
                payment_status=t.payment_status,
                operational_status=t.operational_status,
                vehicle_id=t.vehicle_id,
                garage_id=t.garage_id,
                spot_id=t.spot_id,
                ticket_token=t.ticket_token,
                licence_plate=t.vehicle.licence_plate if t.vehicle else None,
                spot_code=t.spot.code if t.spot else None,
                garage_name=t.garage.name if t.garage else None,
                image_url=t.image_url,
            )
        )
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


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
    try:
        return create_ticket_entry(db, data)
    except (
        InvalidVehicleError,
        InvalidSpotError,
        SpotGarageMismatchError,
        SpotInactiveError,
    ) as e:
        raise HTTPException(400, str(e))
    except (SpotOccupiedError, NoFreeSpotError) as e:
        raise HTTPException(409, str(e))
    except (TicketPersistenceError, TicketTokenRetryExceededError) as e:
        raise HTTPException(500, str(e))


@router.post("/{ticket_id}/exit", response_model=schemas.TicketResponse)
def ticket_exit(
    ticket_id: int, data: schemas.TicketExit, db: Session = Depends(get_db)
):
    try:
        return close_ticket(db, ticket_id, data)
    except TicketNotFoundError as e:
        raise HTTPException(404, str(e))
    except TicketStateError as e:
        raise HTTPException(400, str(e))
