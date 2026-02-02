from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    SmallInteger,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base


class ParkingSpot(Base):
    __tablename__ = "parking_spot"

    id = Column(Integer, primary_key=True)
    garage_id = Column(
        Integer, ForeignKey("parking_config.id"), nullable=False
    )  # u DB ti je bigint, ali radi i kao int
    code = Column(String(50), nullable=False)
    is_rentable = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    rate = Column(Numeric)


class Vehicle(Base):
    __tablename__ = "vehicle"

    id = Column(Integer, primary_key=True)
    licence_plate = Column(String(8), unique=True)
    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.id"))
    created = Column(DateTime, server_default=func.now())
    status = Column(SmallInteger)

    vehicle_type = relationship("VehicleType")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime, nullable=True)
    fee = Column(Numeric)
    ticket_state = Column(String)
    payment_status = Column(String)
    operational_status = Column(String)
    garage_id = Column(Integer)

    spot_id = Column(Integer, ForeignKey("parking_spot.id"), nullable=True)

    vehicle = relationship("Vehicle")
    spot = relationship("ParkingSpot")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    amount = Column(Numeric)
    method = Column(String(20))
    currency = Column(String(3))
    paid_at = Column(DateTime)

    ticket = relationship("Ticket")
