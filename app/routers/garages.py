from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.db import get_db
from app import models, schemas
from app.errors import api_error

router = APIRouter(prefix="/garages", tags=["Garages"])


@router.get(
    "/overview",
    response_model=list[schemas.GarageOverviewRow],
    summary="Garage overview (counts only)",
    description=(
        "Returns one row per garage with spot counts (total, free, occupied, "
        "rentable). Use for dashboard overview without loading full spot "
        "lists. Optional garage_id to filter a single garage."
    ),
)
def garage_overview(
    db: Session = Depends(get_db),
    garage_id: int | None = Query(
        default=None,
        description="If set, return only this garage's overview.",
    ),
):
    # Aggregation in DB: one query for all garages (or one). No spot lists.
    q = text("""
        SELECT
            pc.id AS garage_id,
            pc.name,
            COUNT(p.id)::int AS total_spots,
            COUNT(p.id) FILTER (WHERE p.is_active AND NOT EXISTS (
                SELECT 1 FROM tickets t
                WHERE t.spot_id = p.id AND t.ticket_state = 'OPEN'
            ))::int AS free_spots,
            COUNT(p.id) FILTER (WHERE p.is_active AND EXISTS (
                SELECT 1 FROM tickets t
                WHERE t.spot_id = p.id AND t.ticket_state = 'OPEN'
            ))::int AS occupied_spots,
            COUNT(p.id) FILTER (WHERE p.is_active AND p.is_rentable)::int
                AS rentable_spots
        FROM parking_config pc
        LEFT JOIN parking_spot p ON p.garage_id = pc.id
        WHERE (:garage_id IS NULL OR pc.id = :garage_id)
        GROUP BY pc.id, pc.name
        ORDER BY pc.id
    """)
    rows = db.execute(q, {"garage_id": garage_id}).mappings().all()
    return [schemas.GarageOverviewRow(
        garage_id=r["garage_id"],
        name=r["name"],
        total_spots=r["total_spots"],
        free_spots=r["free_spots"],
        occupied_spots=r["occupied_spots"],
        rentable_spots=r["rentable_spots"],
    ) for r in rows]


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
        raise api_error(404, "GARAGE_NOT_FOUND", "Garage not found.")
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
        created_at=data.created_at if data.created_at else None,
        #
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.put("/{garage_id}", response_model=schemas.GarageResponse)
def update_garage(
    garage_id: int, data: schemas.GarageCreate, db: Session = Depends(get_db)
):
    """Full replace: send all garage fields."""
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise api_error(404, "GARAGE_NOT_FOUND", "Garage not found.")
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


@router.patch("/{garage_id}", response_model=schemas.GarageResponse)
def patch_garage(
    garage_id: int, data: schemas.GarageUpdate, db: Session = Depends(get_db)
):
    """Partial update: send only the fields you want to change."""
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise api_error(404, "GARAGE_NOT_FOUND", "Garage not found.")
    update = data.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(g, key, value)
    db.commit()
    db.refresh(g)
    return g


@router.delete("/{garage_id}")
def delete_garage(garage_id: int, db: Session = Depends(get_db)):
    g = db.get(models.ParkingConfig, garage_id)
    if not g:
        raise api_error(404, "GARAGE_NOT_FOUND", "Garage not found.")
    db.delete(g)
    try:
        db.commit()
        return {"deleted": True}
    except IntegrityError:
        db.rollback()
        raise api_error(
            409,
            "GARAGE_DELETE_CONFLICT",
            "Cannot delete garage because it has parking spots or tickets.",
        )
