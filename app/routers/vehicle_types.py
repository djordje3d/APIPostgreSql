from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app import models, schemas
from app.errors import api_error

router = APIRouter(prefix="/vehicle-types", tags=["Vehicle Types"])
# APIRouter je FastAPI komponenta koja se koristi za definisanje API ruta.
# prefix je prefiks za sve route-ove u ovom routeru.
# tags je lista tagova za sve route-ove u ovom routeru.
# router je APIRouter instance.


# db je SQLAlchemy Session instance.
# Depends je FastAPI komponenta koja se koristi za dependency injection.
# get_db je funkcija koja se koristi za dobavljanje SQLAlchemy Session instance.
# schemas je Pydantic model koji se koristi za serializaciju odgovora.


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.VehicleTypeResponse],
)

# router.get je FastAPI komponenta koja se koristi za definisanje GET route-a.
# response_model je Pydantic model koji se koristi za serializaciju odgovora.
def list_vehicle_types(
    db: Session = Depends(get_db),
    limit: int = Query(
        100, ge=1, le=1000
    ),  # limit je limit za sve route-ove u ovom routeru.
    offset: int = Query(0, ge=0),  # offset je offset za sve route-ove u ovom routeru.
):
    q = db.query(models.VehicleType).order_by(models.VehicleType.id)
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{vt_id}", response_model=schemas.VehicleTypeResponse)
def get_vehicle_type(vt_id: int, db: Session = Depends(get_db)):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise api_error(404, "VEHICLE_TYPE_NOT_FOUND", "Vehicle type not found.")
    return vt


@router.post("", response_model=schemas.VehicleTypeResponse)
def create_vehicle_type(data: schemas.VehicleTypeCreate, db: Session = Depends(get_db)):
    vt = models.VehicleType(type=data.type, rate=data.rate)
    db.add(vt)
    db.commit()
    db.refresh(vt)
    return vt


@router.put("/{vt_id}", response_model=schemas.VehicleTypeResponse)
def update_vehicle_type(
    vt_id: int, data: schemas.VehicleTypeCreate, db: Session = Depends(get_db)
):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise api_error(404, "VEHICLE_TYPE_NOT_FOUND", "Vehicle type not found.")
    vt.type = data.type
    vt.rate = data.rate
    try:
        db.commit()
        db.refresh(vt)
        return vt
    except IntegrityError:
        db.rollback()
        raise api_error(
            409,
            "VEHICLE_TYPE_ALREADY_EXISTS",
            "Vehicle type name already exists.",
        )


@router.delete("/{vt_id}")
def delete_vehicle_type(vt_id: int, db: Session = Depends(get_db)):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise api_error(404, "VEHICLE_TYPE_NOT_FOUND", "Vehicle type not found.")
    db.delete(vt)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise api_error(
            409,
            "VEHICLE_TYPE_DELETE_CONFLICT",
            "Cannot delete vehicle type because vehicles use it.",
        )
