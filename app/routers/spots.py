from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import exists

from app.db import SessionLocal
from app import models

router = APIRouter(prefix="/spots", tags=["Parking Spots"])
#  Tag "Parking Spots" se koristi za dokumentaciju (Swagger UI).


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_spots(  # lista sva mesta, sa filterima
    garage_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    rentable_only: bool = Query(default=False),
    only_free: bool = Query(default=False),
    db: Session = Depends(get_db),
):

    q = db.query(models.ParkingSpot)

    if garage_id is not None:
        q = q.filter(models.ParkingSpot.garage_id == garage_id)
    if active_only:
        q = q.filter(models.ParkingSpot.is_active == True)
    if rentable_only:
        q = q.filter(models.ParkingSpot.is_rentable == True)

    # samo slobodna mesta (bez otvorenih tiketa)
    # ~exists() je isto što i NOT EXISTS u SQL

    if only_free:
        q = q.filter(
            ~exists().where(
                (models.Ticket.spot_id == models.ParkingSpot.id)
                & (models.Ticket.ticket_state == "OPEN")
            )
        )

    return q.order_by(models.ParkingSpot.id.desc()).all()
