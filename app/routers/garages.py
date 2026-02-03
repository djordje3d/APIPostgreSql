from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/garages", tags=["Garages"])


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.GarageResponse],
)
def list_garages(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.ParkingConfig).order_by(models.ParkingConfig.id)
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{garage_id}", response_model=schemas.GarageResponse)
def get_garage(garage_id: int, db: Session = Depends(get_db)):
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise HTTPException(404, "Garage not found")
    return g


@router.post("", response_model=schemas.GarageResponse)
def create_garage(data: schemas.GarageCreate, db: Session = Depends(get_db)):
    g = models.ParkingConfig(
        name=data.name,
        capacity=data.capacity,
        default_rate=data.default_rate,
        lost_ticket_fee=data.lost_ticket_fee,
        night_rate=data.night_rate,
        day_rate=data.day_rate,
        open_time=data.open_time,
        close_time=data.close_time,
        allow_subscription=data.allow_subscription,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.put("/{garage_id}", response_model=schemas.GarageResponse)
def update_garage(
    garage_id: int, data: schemas.GarageCreate, db: Session = Depends(get_db)
):
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise HTTPException(404, "Garage not found")
    g.name = data.name
    g.capacity = data.capacity
    g.default_rate = data.default_rate
    g.lost_ticket_fee = data.lost_ticket_fee
    g.night_rate = data.night_rate
    g.day_rate = data.day_rate
    g.open_time = data.open_time
    g.close_time = data.close_time
    g.allow_subscription = data.allow_subscription
    db.commit()
    db.refresh(g)
    return g


@router.delete("/{garage_id}")
def delete_garage(garage_id: int, db: Session = Depends(get_db)):
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise HTTPException(404, "Garage not found")
    db.delete(g)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            400, "Cannot delete garage: it has parking spots or tickets"
        )
