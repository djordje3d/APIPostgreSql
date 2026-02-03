from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class VehicleTypeCreate(BaseModel):
    type: str = Field(..., min_length=1)
    rate: Decimal = Field(...)


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


class GarageCreate(BaseModel):
    name: str
    capacity: int
    default_rate: Decimal
    lost_ticket_fee: Decimal | None = None
    night_rate: Decimal | None = None
    day_rate: Decimal | None = None
    open_time: datetime | None = None
    close_time: datetime | None = None
    allow_subscription: bool | None = True
