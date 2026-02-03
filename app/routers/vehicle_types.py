from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/vehicle-types", tags=["Vehicle Types"])


@router.get(
    "",
    response_model=schemas.PaginatedResponse[schemas.VehicleTypeResponse],
)
def list_vehicle_types(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
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
        raise HTTPException(404, "VehicleType not found")
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
        raise HTTPException(404, "VehicleType not found")
    vt.type = data.type
    vt.rate = data.rate
    try:
        db.commit()
        db.refresh(vt)
        return vt
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Vehicle type name already exists")


@router.delete("/{vt_id}")
def delete_vehicle_type(vt_id: int, db: Session = Depends(get_db)):
    vt = db.get(models.VehicleType, vt_id)
    if not vt:
        raise HTTPException(404, "VehicleType not found")
    db.delete(vt)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Cannot delete: vehicles use this type")
