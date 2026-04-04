from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import USE_API_FEE_CALCULATION
from app.services.pricing import get_ticket_fee
from app.services.spots import allocate_free_spot
from app.services.tokens import generate_ticket_token

MAX_RETRIES = 5


class TicketServiceError(Exception):
    """Base service error for ticket operations."""


class TicketNotFoundError(TicketServiceError):
    pass


class InvalidVehicleError(TicketServiceError):
    pass


class InvalidSpotError(TicketServiceError):
    pass


class SpotGarageMismatchError(TicketServiceError):
    pass


class SpotInactiveError(TicketServiceError):
    pass


class SpotOccupiedError(TicketServiceError):
    pass


class NoFreeSpotError(TicketServiceError):
    pass


class TicketStateError(TicketServiceError):
    pass


class TicketTokenRetryExceededError(TicketServiceError):
    pass


class TicketPersistenceError(TicketServiceError):
    pass


def _resolve_spot_id(db: Session, data: schemas.TicketEntry) -> int:
    spot_id = data.spot_id

    if spot_id is not None:
        spot = db.get(models.ParkingSpot, spot_id)
        if not spot:
            raise InvalidSpotError("Invalid spot_id")
        if spot.garage_id != data.garage_id:
            raise SpotGarageMismatchError("spot_id does not belong to garage")
        if not spot.is_active:
            raise SpotInactiveError("Spot is not active")

        occupied = (
            db.query(models.Ticket)
            .filter(
                models.Ticket.spot_id == spot_id,
                models.Ticket.ticket_state == "OPEN",
            )
            .first()
        )
        if occupied:
            raise SpotOccupiedError("Spot is occupied")
        return spot_id

    try:
        return allocate_free_spot(
            db,
            data.garage_id,
            rentable_only=data.rentable_only,
        )
    except ValueError as exc:
        raise NoFreeSpotError(str(exc)) from exc


def create_ticket_entry(
    db: Session, data: schemas.TicketEntry
) -> models.Ticket:
    vehicle = db.get(models.Vehicle, data.vehicle_id)
    if not vehicle:
        raise InvalidVehicleError("Invalid vehicle_id")

    spot_id = _resolve_spot_id(db, data)

    for _ in range(MAX_RETRIES):
        try:
            ticket = models.Ticket(
                ticket_token=generate_ticket_token(data.garage_id),
                vehicle_id=data.vehicle_id,
                entry_time=data.entry_time or datetime.now(timezone.utc),
                ticket_state="OPEN",
                payment_status="NOT_APPLICABLE",
                operational_status="OK",
                garage_id=data.garage_id,
                fee=0,
                spot_id=spot_id,
                image_url=data.image_url,
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket
        except IntegrityError as exc:
            db.rollback()
            error_text = str(exc.orig).lower()
            if "ticket_token" not in error_text:
                raise TicketPersistenceError(
                    f"Database integrity error: {str(exc.orig)}"
                ) from exc

    raise TicketTokenRetryExceededError(
        "Failed to generate unique ticket token after multiple retries"
    )


def _validate_spot_reassignment(
    db: Session, ticket: models.Ticket, new_spot_id: int
) -> None:
    if new_spot_id == ticket.spot_id:
        return
    spot = db.get(models.ParkingSpot, new_spot_id)
    if not spot:
        raise InvalidSpotError("Invalid spot_id")
    if spot.garage_id != ticket.garage_id:
        raise SpotGarageMismatchError("spot_id does not belong to garage")
    if not spot.is_active:
        raise SpotInactiveError("Spot is not active")
    occupied = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.spot_id == new_spot_id,
            models.Ticket.ticket_state == "OPEN",
            models.Ticket.id != ticket.id,
        )
        .first()
    )
    if occupied:
        raise SpotOccupiedError("Spot is occupied")


def apply_ticket_update(
    db: Session, ticket_id: int, data: schemas.TicketUpdate
) -> models.Ticket:
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise TicketNotFoundError("Ticket not found")

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return ticket

    if "operational_status" in updates:
        ticket.operational_status = updates["operational_status"]

    if "image_url" in updates:
        ticket.image_url = updates["image_url"]

    if "spot_id" in updates:
        if ticket.ticket_state != "OPEN":
            raise TicketStateError("Spot can only be changed on open tickets")
        new_sid = updates["spot_id"]
        if new_sid is None:
            raise InvalidSpotError("spot_id cannot be cleared")
        _validate_spot_reassignment(db, ticket, new_sid)
        ticket.spot_id = new_sid

    db.commit()
    db.refresh(ticket)
    return ticket


def close_ticket(
    db: Session, ticket_id: int, data: schemas.TicketExit
) -> models.Ticket:
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise TicketNotFoundError("Ticket not found")

    if ticket.ticket_state != "OPEN" or ticket.exit_time is not None:
        raise TicketStateError("Ticket is not open")

    ticket.exit_time = data.exit_time or datetime.now(timezone.utc)
    ticket.ticket_state = "CLOSED"
    if USE_API_FEE_CALCULATION:
        ticket.fee = get_ticket_fee(ticket, db)

    db.commit()
    db.refresh(ticket)
    return ticket
