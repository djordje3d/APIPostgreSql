from fastapi import FastAPI

from app.routers.tickets import router as tickets_router
from app.routers.payments import router as payments_router
from app.routers.vehicles import router as vehicles_router
from app.routers.vehicle_types import router as vehicle_types_router
from app.routers.spots import router as spots_router

app = FastAPI(title="Parking API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(vehicle_types_router)
app.include_router(vehicles_router)
app.include_router(tickets_router)
app.include_router(payments_router)
app.include_router(spots_router)
