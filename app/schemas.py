from typing import Any, Literal, Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, time
from decimal import Decimal

# --- Response models (for list/detail endpoints; from_attributes for ORM) ---


class GarageOverviewRow(BaseModel):
    """Per-garage spot counts for dashboard overview (no spot lists)."""
    garage_id: int
    name: str
    total_spots: int
    free_spots: int
    occupied_spots: int
    rentable_spots: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class GarageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    capacity: int
    default_rate: Decimal
    lost_ticket_fee: Decimal | None
    night_rate: Decimal | None
    day_rate: Decimal | None
    open_time: time | None
    close_time: time | None
    allow_subscription: bool | None
    created_at: datetime | None


class VehicleTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    rate: float  # serialized as JSON number for frontend math/sort/compare


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    licence_plate: str | None
    vehicle_type_id: int | None
    created: datetime | None
    status: int


class SpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    garage_id: int
    code: str
    is_rentable: bool
    is_active: bool


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entry_time: datetime | None
    exit_time: datetime | None
    fee: Decimal | None
    ticket_state: str | None
    payment_status: str | None
    operational_status: str | None
    vehicle_id: int | None
    garage_id: int
    spot_id: int | None
    image_url: str | None = None
    ticket_token: str


class TicketDashboardRow(BaseModel):
    """Ticket list row with licence_plate and spot_code for dashboard."""

    id: int
    entry_time: datetime | None
    exit_time: datetime | None
    fee: Decimal | None
    ticket_state: str | None
    payment_status: str | None
    operational_status: str | None
    vehicle_id: int | None
    garage_id: int
    spot_id: int | None
    ticket_token: str
    licence_plate: str | None = None
    spot_code: str | None = None
    garage_name: str | None = None
    vehicle_type: str | None = None
    image_url: str | None = None
    rest_to_pay: float = 0.0


class DashboardAnalyticsResponse(BaseModel):
    """Single response for status cards + revenue summary."""

    free_spots: int
    occupied_spots: int
    inactive_spots: int
    open_tickets: int
    today_revenue: float
    month_revenue: float
    unpaid_partially_paid_count: int
    total_outstanding: float


# --- Pagination ---
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    items: list[T]


# DB CHECK constraint values — use in query params and any request body
# that accepts these
TicketState = Literal["OPEN", "CLOSED"]
PaymentStatus = Literal["NOT_APPLICABLE", "UNPAID", "PARTIALLY_PAID", "PAID"]
OperationalStatus = Literal[
    "OK", "UNRECOGNIZED_PLATE", "POLICE_SUPERVISION", "MALFUNCTION"
]


class VehicleTypeCreate(BaseModel):
    type: str = Field(..., min_length=1)
    rate: Decimal = Field(...)


class VehicleCreate(BaseModel):
    licence_plate: str | None = None
    vehicle_type_id: int
    status: int = 1


class VehicleUpdate(BaseModel):
    licence_plate: str | None = None
    status: int | None = None
    vehicle_type_id: int | None = None


class TicketEntry(BaseModel):
    vehicle_id: int
    entry_time: datetime | None = None
    garage_id: int

    spot_id: int | None = None  # ako želiš ručno dodeljivanje
    rentable_only: bool = False  # ako želiš da bira samo is_rentable mesta
    image_url: str | None = None


class TicketExit(BaseModel):
    exit_time: datetime | None = None


class TicketUpdate(BaseModel):
    """Partial update with domain-safe fields only.

    Lifecycle fields (ticket_state, payment_status, fee, entry_time) are
    controlled by entry/exit and payment flows — not by this endpoint.
    garage_id cannot be changed; use operational notes, image, or spot
    reassignment on OPEN tickets only.
    """

    model_config = ConfigDict(extra="forbid")

    operational_status: OperationalStatus | None = None
    spot_id: int | None = None
    image_url: str | None = Field(None, max_length=512)


class PaymentCreate(BaseModel):
    ticket_id: int
    amount: Decimal = Field(gt=0)  # uplata mora biti > 0
    method: str
    currency: str = "RSD"
    paid_at: datetime | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int | None
    amount: Decimal
    method: str | None
    currency: str
    paid_at: datetime | None


class OutstandingResponse(BaseModel):
    """Total amount still to be paid.

    For unpaid/partially paid tickets (optionally per garage).
    """
    total_outstanding: float


class PaymentUpdate(BaseModel):
    amount: Decimal = Field(gt=0)
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
    open_time: time | None = None
    close_time: time | None = None
    allow_subscription: bool | None = True
    created_at: datetime | None = None


class GarageUpdate(BaseModel):
    """All fields optional for PATCH partial updates."""

    name: str | None = None
    capacity: int | None = None
    default_rate: Decimal | None = None
    lost_ticket_fee: Decimal | None = None
    night_rate: Decimal | None = None
    day_rate: Decimal | None = None
    open_time: time | None = None
    close_time: time | None = None
    allow_subscription: bool | None = None


class SpotCreate(BaseModel):
    garage_id: int
    code: str = Field(..., max_length=14)
    is_rentable: bool = False
    is_active: bool = True


class SpotUpdate(BaseModel):
    code: str | None = Field(None, max_length=14)
    is_rentable: bool | None = None
    is_active: bool | None = None
