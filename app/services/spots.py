from sqlalchemy import text
from sqlalchemy.orm import Session


def allocate_free_spot(
    db: Session,
    garage_id: int,
    rentable_only: bool = False
  ) -> int:
    """
    Vrati ID slobodnog spota za dati garage_id.
    Slobodan = is_active AND nije vezan za OPEN ticket.
    Koristi FOR UPDATE SKIP LOCKED da izbegne race kad više entry poziva dođe odjednom.
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
    FOR UPDATE OF ps SKIP LOCKED -- zaštita od race condition-a kad više entry poziva dođe odjednom.
    LIMIT 1
    """

    spot_id = db.execute(
        text(sql),
        {"garage_id": garage_id, "rentable_only": rentable_only},
    ).scalar()
    # vraca ID slobodnog spota ili None ako nema slobodnih spota.
    # Ne mora biti samo jedan spot, ako ima više slobodnih, vraca ID prvog slobodnog spota. 
    # Kako je ORDER BY ps.id, vraca ID najmanjeg slobodnog spota.

    if spot_id is None:
        raise ValueError("No free spots available")

    return int(spot_id)
