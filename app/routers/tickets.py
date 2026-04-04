from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app import models, schemas
from app.services.dashboard_analytics import (
    batch_payment_totals_by_ticket,
    compute_rest_to_pay_for_ticket,
)
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
    apply_ticket_update,
    close_ticket,
    create_ticket_entry,
)
from app.errors import api_error

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/dashboard",
    response_model=schemas.PaginatedResponse[schemas.TicketDashboardRow],
)
def list_tickets_dashboard(
    db: Session = Depends(get_db),
    garage_id: int | None = Query(default=None),
    ticket_state: schemas.TicketState | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    """List tickets with licence_plate and spot_code for dashboard."""
    q = (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.vehicle).joinedload(
                models.Vehicle.vehicle_type
            ),
            joinedload(models.Ticket.spot),
            joinedload(models.Ticket.garage),
        )
        .order_by(models.Ticket.id.desc())
    )
    if garage_id is not None:
        q = q.filter(models.Ticket.garage_id == garage_id)
    if ticket_state is not None:
        q = q.filter(models.Ticket.ticket_state == ticket_state)
    if from_date is not None:
        start = datetime.fromisoformat(
            from_date.isoformat() + "T00:00:00+00:00"
        )
        q = q.filter(models.Ticket.entry_time >= start)
    if to_date is not None:
        end_exclusive = datetime.fromisoformat(
            (to_date + timedelta(days=1)).isoformat() + "T00:00:00+00:00"
        )
        q = q.filter(models.Ticket.entry_time < end_exclusive)
    total = q.count()
    tickets = q.limit(limit).offset(offset).all()
    pay_map = batch_payment_totals_by_ticket(db, [t.id for t in tickets])
    items = []
    for t in tickets:
        # Use computed fee when entry_time and exit_time are set, so direct DB
        # changes to entry/exit are reflected after refresh
        # (dashboard display only).
        fee = t.fee
        if t.entry_time is not None and t.exit_time is not None:
            fee = get_ticket_fee(t, db)
        paid = pay_map.get(t.id, 0.0)
        rest = compute_rest_to_pay_for_ticket(db, t, paid)
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
                vehicle_type=(
                    t.vehicle.vehicle_type.type
                    if t.vehicle and t.vehicle.vehicle_type
                    else None
                ),
                image_url=t.image_url,
                rest_to_pay=rest,
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
        raise api_error(404, "TICKET_NOT_FOUND", "Ticket not found.")
    return t


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int,
    data: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    try:
        return apply_ticket_update(db, ticket_id, data)
    except TicketNotFoundError:
        raise api_error(404, "TICKET_NOT_FOUND", "Ticket not found.")
    except InvalidSpotError as e:
        raise api_error(400, "INVALID_SPOT_UPDATE", str(e))
    except SpotGarageMismatchError:
        raise api_error(
            409,
            "SPOT_GARAGE_MISMATCH",
            "Selected parking spot does not belong to this ticket's garage.",
        )
    except SpotInactiveError:
        raise api_error(409, "SPOT_INACTIVE", "Selected parking spot is inactive.")
    except SpotOccupiedError:
        raise api_error(
            409,
            "SPOT_OCCUPIED",
            "The selected parking spot is already occupied.",
        )
    except TicketStateError as e:
        raise api_error(409, "TICKET_NOT_OPEN", str(e))


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Ticket, ticket_id)
    if not t:
        raise api_error(404, "TICKET_NOT_FOUND", "Ticket not found.")
    db.delete(t)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise api_error(
            409,
            "TICKET_DELETE_CONFLICT",
            "Cannot delete ticket because it has payments.",
        )


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
        if isinstance(e, InvalidVehicleError):
            raise api_error(404, "VEHICLE_NOT_FOUND", "Vehicle does not exist.")
        if isinstance(e, InvalidSpotError):
            raise api_error(404, "SPOT_NOT_FOUND", "Parking spot does not exist.")
        if isinstance(e, SpotGarageMismatchError):
            raise api_error(
                409,
                "SPOT_GARAGE_MISMATCH",
                "Selected parking spot does not belong to selected garage.",
            )
        raise api_error(409, "SPOT_INACTIVE", "Selected parking spot is inactive.")
    except (SpotOccupiedError, NoFreeSpotError) as e:
        if isinstance(e, SpotOccupiedError):
            raise api_error(
                409,
                "SPOT_OCCUPIED",
                "The selected parking spot is already occupied.",
            )
        raise api_error(
            409,
            "NO_FREE_SPOTS_AVAILABLE",
            "No free spots available for this garage.",
        )
    except (TicketPersistenceError, TicketTokenRetryExceededError) as e:
        raise api_error(
            500,
            "DATABASE_ERROR",
            "Ticket could not be saved.",
            details={"reason": e.__class__.__name__},
        )


@router.post("/{ticket_id}/exit", response_model=schemas.TicketResponse)
def ticket_exit(
    ticket_id: int, data: schemas.TicketExit, db: Session = Depends(get_db)
):
    try:
        return close_ticket(db, ticket_id, data)
    except TicketNotFoundError:
        raise api_error(404, "TICKET_NOT_FOUND", "Ticket not found.")
    except TicketStateError:
        raise api_error(
            409,
            "TICKET_ALREADY_CLOSED",
            "Ticket is not open.",
        )
