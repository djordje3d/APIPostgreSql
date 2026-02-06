from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.routers.tickets import router as tickets_router
from app.routers.payments import router as payments_router
from app.routers.vehicles import router as vehicles_router
from app.routers.vehicle_types import router as vehicle_types_router
from app.routers.spots import router as spots_router
from app.routers.garages import router as garages_router

app = FastAPI(
    title="Parking API",
    description=(
        "API for managing parking garages, spots, vehicles, tickets, and "
        "payments. Supports entry/exit flow, spot allocation, and payment "
        "recording for closed tickets."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Garages", "description": "Garage (config) management."},
        {"name": "Vehicle Types", "description": "Vehicle type definitions and rates."},
        {"name": "Vehicles", "description": "Vehicle registry (plate, type, status)."},
        {
            "name": "Tickets",
            "description": "Entry, exit, list; filter by state/garage.",
        },
        {"name": "Payments", "description": "Payments for closed tickets."},
        {
            "name": "Parking Spots",
            "description": "Spots per garage; list, create, update.",
        },
    ],
)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health check. Returns 200 if app and DB are OK, 503 if DB is unavailable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


app.include_router(garages_router)
app.include_router(vehicle_types_router)
app.include_router(vehicles_router)
app.include_router(tickets_router)
app.include_router(payments_router)
app.include_router(spots_router)
