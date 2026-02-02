from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class VehicleTypeCreate(BaseModel):
    type: str
    rate: Decimal


class VehicleCreate(BaseModel):
    licence_plate: str
    vehicle_type_id: int
    status: int = 1


class TicketEntry(BaseModel):
    vehicle_id: int
    entry_time: datetime | None = None
    garage_id: int

    spot_id: int | None = None  # ako želiš ručno dodeljivanje
    rentable_only: bool = False  # ako želiš da bira samo is_rentable mesta


class TicketExit(BaseModel):
    exit_time: datetime | None = None


class PaymentCreate(BaseModel):
    ticket_id: int
    amount: Decimal = Field(gt=0)  # uplata mora biti > 0
    method: str
    currency: str = "RSD"
    paid_at: datetime | None = None
