from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exists

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/spots", tags=["Parking Spots"])
# Tag "Parking Spots" je za dokumentaciju (Swagger UI).


@router.get("")
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


@router.get("/{spot_id}")
def get_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.get(models.ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(404, "Spot not found")
    return spot


@router.post("")
def create_spot(data: schemas.SpotCreate, db: Session = Depends(get_db)):
    garage = db.get(models.ParkingConfig, data.garage_id)
    if not garage:
        raise HTTPException(400, "Invalid garage_id")

    spot = models.ParkingSpot(
        garage_id=data.garage_id,
        code=data.code,
        is_rentable=data.is_rentable,
        is_active=data.is_active,
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot


@router.patch("/{spot_id}")
def update_spot(spot_id: int, data: schemas.SpotUpdate, db: Session = Depends(get_db)):
    spot = db.get(models.ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(404, "Spot not found")

    if data.code is not None:
        spot.code = data.code
    if data.is_rentable is not None:
        spot.is_rentable = data.is_rentable
    if data.is_active is not None:
        spot.is_active = data.is_active

    db.commit()
    db.refresh(spot)
    return spot
