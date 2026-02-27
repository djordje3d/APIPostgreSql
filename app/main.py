# pyright: reportMissingImports=false
# Import config first so load_dotenv() runs before db engine is created.
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import (
    API_KEY,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_MAX_AGE,
    CORS_DISABLED,
    CORS_ORIGINS,
)
from app.db import get_db
from app.auth import APIKeyMiddleware
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

# CORS: allow browser apps (different origin) to call this API. Skip if CORS_DISABLED.
if not CORS_DISABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
        max_age=CORS_MAX_AGE,
    )
app.add_middleware(APIKeyMiddleware)


def openapi_with_api_key():
    """When API_KEY is set, add X-API-Key to OpenAPI so Swagger UI shows Authorize and sends the header. /health is documented as public (no key required)."""
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    if API_KEY:
        schema.setdefault("components", {})["securitySchemes"] = {
            "ApiKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Required for all endpoints except GET /health when API_KEY is set in .env.",
            },
        }
        schema["security"] = [{"ApiKeyHeader": []}]
        # /health is public; don't require API key in Swagger for it
        if "paths" in schema and "/health" in schema["paths"] and "get" in schema["paths"]["/health"]:
            schema["paths"]["/health"]["get"]["security"] = []
    return schema


app.openapi = openapi_with_api_key


@app.get("/")
def root():
    """Simple liveness check; does not use the database."""
    return {"message": "Parking API", "docs": "/docs"}


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
