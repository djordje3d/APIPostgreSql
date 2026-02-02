from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Vehicle).order_by(models.Vehicle.id).all()


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


@router.get("/by-plate/{plate}")
def get_vehicle_by_plate(plate: str, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.licence_plate == plate).first()
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


@router.post("")
def create_vehicle(data: schemas.VehicleCreate, db: Session = Depends(get_db)):
    # ensure vehicle_type exists
    vt = db.get(models.VehicleType, data.vehicle_type_id)
    if not vt:
        raise HTTPException(400, "Invalid vehicle_type_id")

    # ensure plate unique
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


@router.patch("/{vehicle_id}")
def patch_vehicle(vehicle_id: int, payload: dict, db: Session = Depends(get_db)):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")

    if "status" in payload:
        v.status = int(payload["status"])
    if "vehicle_type_id" in payload:
        vt = db.get(models.VehicleType, int(payload["vehicle_type_id"]))
        if not vt:
            raise HTTPException(400, "Invalid vehicle_type_id")
        v.vehicle_type_id = int(payload["vehicle_type_id"])

    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(models.Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    db.delete(v)
    db.commit()
    return {"deleted": True}
