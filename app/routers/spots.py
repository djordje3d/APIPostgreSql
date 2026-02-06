from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/spots", tags=["Parking Spots"])
# Tag "Parking Spots" je za dokumentaciju (Swagger UI).


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.SpotResponse],
)
def list_spots(
    db: Session = Depends(get_db),
    garage_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    rentable_only: bool = Query(default=False),
    only_free: bool = Query(default=False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.ParkingSpot)

    if garage_id is not None:
        q = q.filter(models.ParkingSpot.garage_id == garage_id)
    if active_only:
        q = q.filter(models.ParkingSpot.is_active == True)
    if rentable_only:
        q = q.filter(models.ParkingSpot.is_rentable == True)
    if only_free:
        q = q.filter(
            ~exists().where(
                (models.Ticket.spot_id == models.ParkingSpot.id)
                & (models.Ticket.ticket_state == "OPEN")
            )
        )

    q = q.order_by(models.ParkingSpot.id.desc())
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{spot_id}", response_model=schemas.SpotResponse)
def get_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.get(models.ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(404, "Spot not found")
    return spot


@router.post("", response_model=schemas.SpotResponse)
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
    try:
        db.commit()
        db.refresh(spot)
        return spot
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Spot code already exists for this garage")


@router.patch("/{spot_id}", response_model=schemas.SpotResponse)
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

    try:
        db.commit()
        db.refresh(spot)
        return spot
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Spot code already exists for this garage")


@router.delete("/{spot_id}")
def delete_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.get(models.ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(404, "Spot not found")

    # zabrani ako postoji aktivan tiket
    has_open_ticket = db.query(
        exists().where(
            (models.Ticket.spot_id == spot_id) & (models.Ticket.ticket_state == "OPEN")
        )
    ).scalar()

    if has_open_ticket:
        raise HTTPException(400, "Cannot deactivate spot: it has an OPEN ticket")

    spot.is_active = False
    db.commit()
    return {"message": "Parking spot successfully deactivated", "spot_id": spot_id}


@router.patch("/{spot_id}/activate", response_model=schemas.SpotResponse)
def activate_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.get(models.ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(404, "Spot not found")
    spot.is_active = True
    db.commit()
    db.refresh(spot)
    return spot
