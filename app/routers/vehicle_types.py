from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/vehicle-types", tags=["Vehicle Types"])


@router.get("")
def list_vehicle_types(db: Session = Depends(get_db)):
    return db.query(models.VehicleType).order_by(models.VehicleType.id).all()


@router.get("/{vt_id}")
def get_vehicle_type(vt_id: int, db: Session = Depends(get_db)):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise HTTPException(404, "VehicleType not found")
    return vt


@router.post("")
def create_vehicle_type(data: schemas.VehicleTypeCreate, db: Session = Depends(get_db)):
    vt = models.VehicleType(type=data.type, rate=data.rate)
    db.add(vt)
    db.commit()
    db.refresh(vt)
    return vt


@router.put("/{vt_id}")
def update_vehicle_type(
    vt_id: int, data: schemas.VehicleTypeCreate, db: Session = Depends(get_db)
):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise HTTPException(404, "VehicleType not found")
    vt.type = data.type
    vt.rate = data.rate
    db.commit()
    db.refresh(vt)
    return vt


@router.delete("/{vt_id}")
def delete_vehicle_type(vt_id: int, db: Session = Depends(get_db)):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise HTTPException(404, "VehicleType not found")
    db.delete(vt)
    db.commit()
    return {"deleted": True}
