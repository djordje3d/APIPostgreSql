from collections.abc import Sequence

from sqlalchemy import exists, text
from sqlalchemy.orm import Session

from app import models, schemas


def spot_ids_with_open_tickets(
    db: Session, spot_ids: Sequence[int]
) -> set[int]:
    ids = [i for i in spot_ids if i is not None]
    if not ids:
        return set()
    rows = (
        db.query(models.Ticket.spot_id)
        .filter(
            models.Ticket.spot_id.in_(ids),
            models.Ticket.ticket_state == "OPEN",
            models.Ticket.spot_id.isnot(None),
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def spot_is_occupied(db: Session, spot_id: int) -> bool:
    return bool(
        db.query(
            exists().where(
                (models.Ticket.spot_id == spot_id)
                & (models.Ticket.ticket_state == "OPEN")
            )
        ).scalar()
    )


def to_spot_response(
    db: Session,
    spot: models.ParkingSpot,
    *,
    occupied: bool | None = None,
) -> schemas.SpotResponse:
    if occupied is None:
        occupied = spot_is_occupied(db, spot.id)
    return schemas.SpotResponse(
        id=spot.id,
        garage_id=spot.garage_id,
        code=spot.code,
        is_rentable=spot.is_rentable,
        is_active=spot.is_active,
        is_occupied=occupied,
    )


def allocate_free_spot(
    db: Session,
    garage_id: int,
    rentable_only: bool = False
  ) -> int:
    """
    Vrati ID slobodnog spota za dati garage_id.
    Slobodan = is_active AND nije vezan za OPEN ticket.
    Koristi FOR UPDATE SKIP LOCKED da izbegne race kad više entry poziva
    dođe odjednom.
    """
    sql = """
    SELECT ps.id
    FROM parking_spot ps
    WHERE ps.garage_id = :garage_id
      AND ps.is_active = true
      AND (:rentable_only = false OR ps.is_rentable = true)
      AND NOT EXISTS (
        SELECT 1
        FROM tickets t
        WHERE t.spot_id = ps.id
          AND t.ticket_state = 'OPEN'
      )
    ORDER BY ps.id
    FOR UPDATE OF ps SKIP LOCKED -- zaštita od race pri istovremenom entry-u.
    LIMIT 1
    """

    spot_id = db.execute(
        text(sql),
        {"garage_id": garage_id, "rentable_only": rentable_only},
    ).scalar()
    # vraca ID slobodnog spota ili None ako nema slobodnih spota.
    # Ne mora biti samo jedan spot, ako ima više slobodnih, vraca ID prvog.
    # Kako je ORDER BY ps.id, vraca ID najmanjeg slobodnog spota.

    if spot_id is None:
        raise ValueError("No free spots available")

    return int(spot_id)
