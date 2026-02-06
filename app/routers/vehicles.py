from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.VehicleResponse],
)
def list_vehicles(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.Vehicle).order_by(models.Vehicle.id)
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PaginatedResponse(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/by-plate/{plate}", response_model=schemas.VehicleResponse)
def get_vehicle_by_plate(plate: str, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.licence_plate == plate).first()
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


@router.get("/{vehicle_id}", response_model=schemas.VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


@router.post("", response_model=schemas.VehicleResponse)
def create_vehicle(data: schemas.VehicleCreate, db: Session = Depends(get_db)):
    # ensure vehicle_type exists
    vt = db.get(models.VehicleType, data.vehicle_type_id)
    if not vt:
        raise HTTPException(400, "Invalid vehicle_type_id")

    # ensure plate unique only when provided (multiple vehicles may have no plate)
    if data.licence_plate is not None:
        exists = (
            db.query(models.Vehicle)
            .filter(models.Vehicle.licence_plate == data.licence_plate)
            .first()
        )
        if exists:
            raise HTTPException(400, "licence_plate already exists")

    v = models.Vehicle(
        licence_plate=data.licence_plate,
        vehicle_type_id=data.vehicle_type_id,
        status=data.status,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.patch("/{vehicle_id}", response_model=schemas.VehicleResponse)
def patch_vehicle(
    vehicle_id: int,
    data: schemas.VehicleUpdate,
    db: Session = Depends(get_db),
):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")

    if data.licence_plate is not None:
        v.licence_plate = data.licence_plate
    if data.status is not None:
        v.status = data.status
    if data.vehicle_type_id is not None:
        vt = db.get(models.VehicleType, data.vehicle_type_id)
        if not vt:
            raise HTTPException(400, "Invalid vehicle_type_id")
        v.vehicle_type_id = data.vehicle_type_id

    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    db.delete(v)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Cannot delete: vehicle has tickets")
