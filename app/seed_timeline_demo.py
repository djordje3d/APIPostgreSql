from datetime import datetime, timedelta, timezone
import random

from app.db import SessionLocal
from app import models
from app.services.tokens import generate_ticket_token


GARAGE_ID = 1
DAYS_BACK = 30
MIN_TICKETS_PER_DAY = 10
MAX_TICKETS_PER_DAY = 35
PLATE_PREFIX = "BZ"  # easy cleanup later


def make_plate(n: int) -> str:
    # max length in your model is 8 chars
    return f"{PLATE_PREFIX}{n:06d}"[:8]


def main():
    db = SessionLocal()
    try:
        vehicle_types = (
            db.query(models.VehicleType).order_by(models.VehicleType.id).all()
        )
        if not vehicle_types:
            print("No vehicle types found. Create vehicle types first.")
            return

        spots = (
            db.query(models.ParkingSpot)
            .filter(
                models.ParkingSpot.garage_id == GARAGE_ID,
                models.ParkingSpot.is_active == True,
            )
            .all()
        )
        if not spots:
            print(f"No active spots found for garage_id={GARAGE_ID}.")
            return

        created_vehicles = 0
        created_tickets = 0

        now = datetime.now(timezone.utc)
        start_day = (now - timedelta(days=DAYS_BACK - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        plate_counter = 1

        for day_index in range(DAYS_BACK):
            day_start = start_day + timedelta(days=day_index)

            # small day-to-day variation to make curves visible
            base_count = random.randint(MIN_TICKETS_PER_DAY, MAX_TICKETS_PER_DAY)

            for _ in range(base_count):
                vt = random.choice(vehicle_types)

                plate = make_plate(plate_counter)
                plate_counter += 1

                vehicle = models.Vehicle(
                    licence_plate=plate,
                    vehicle_type_id=vt.id,
                    status=1,
                )
                db.add(vehicle)
                db.flush()  # get vehicle.id without full commit
                created_vehicles += 1

                entry_time = day_start + timedelta(
                    hours=random.randint(6, 22),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )

                stay_minutes = random.randint(20, 8 * 60)
                exit_time = entry_time + timedelta(minutes=stay_minutes)

                spot = random.choice(spots)

                ticket = models.Ticket(
                    ticket_token=generate_ticket_token(GARAGE_ID),
                    entry_time=entry_time,
                    exit_time=exit_time,
                    fee=0,  # dashboard recalculates closed ticket fee for display
                    ticket_state="CLOSED",
                    payment_status="UNPAID",
                    operational_status="OK",
                    vehicle_id=vehicle.id,
                    garage_id=GARAGE_ID,
                    spot_id=spot.id,
                    image_url=None,
                )
                db.add(ticket)
                created_tickets += 1

            # commit once per day
            db.commit()
            print(f"Day {day_index + 1}/{DAYS_BACK} committed.")

        print()
        print(f"Created vehicles: {created_vehicles}")
        print(f"Created tickets:  {created_tickets}")
        print("Done.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
