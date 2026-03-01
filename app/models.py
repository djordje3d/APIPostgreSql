from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Time,
    ForeignKey,
    SmallInteger,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from .db import Base


class ParkingSpot(Base):
    __tablename__ = "parking_spot"
    __table_args__ = (UniqueConstraint("garage_id", "code", name="uq_spot_per_garage"),)

    id = Column(Integer, primary_key=True)
    garage_id = Column(
        Integer, ForeignKey("parking_config.id"), nullable=False
    )  # u DB ti je bigint, ali radi i kao int
    code = Column(String(14), nullable=False, server_default=text("'10010'"))
    is_rentable = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)


class ParkingConfig(Base):
    __tablename__ = "parking_config"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    default_rate = Column(Numeric, nullable=False)
    lost_ticket_fee = Column(Numeric, nullable=True)
    night_rate = Column(Numeric, nullable=True)
    day_rate = Column(Numeric, nullable=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    allow_subscription = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, unique=True)
    rate = Column(Numeric, nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicle"

    id = Column(Integer, primary_key=True)
    licence_plate = Column(String(8), unique=True, nullable=True)
    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.id"), nullable=True)
    created = Column(DateTime, server_default=func.now())
    status = Column(SmallInteger, default=1)

    vehicle_type = relationship("VehicleType")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)

    entry_time = Column(DateTime)
    exit_time = Column(DateTime, nullable=True)
    fee = Column(Numeric)
    ticket_state = Column(String, nullable=False)
    payment_status = Column(String, nullable=False)
    operational_status = Column(String, nullable=False)

    vehicle_id = Column(Integer, ForeignKey("vehicle.id"))
    garage_id = Column(Integer, ForeignKey("parking_config.id"), nullable=False)
    spot_id = Column(Integer, ForeignKey("parking_spot.id"), nullable=True)

    vehicle = relationship("Vehicle")
    spot = relationship("ParkingSpot")
    garage = relationship("ParkingConfig")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    amount = Column(Numeric, nullable=False)
    method = Column(String(20), nullable=True)
    currency = Column(String(3), nullable=False, server_default=text("'RSD'"))
    paid_at = Column(DateTime, server_default=func.now())

    ticket = relationship("Ticket")
