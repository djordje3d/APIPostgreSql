import math
from datetime import timedelta
from decimal import Decimal


# delta
def calculate_fee(ticket, db) -> Decimal:
    delta: timedelta = ticket.exit_time - ticket.entry_time
    minutes = max(1, int(delta.total_seconds() / 60))
    hours = max(1, math.ceil(minutes / 60))

    rate = Decimal(ticket.vehicle.vehicle_type.rate)
    return hours * rate


# NOTE: This function is never called; fee is set by DB trigger.
# It’s kept for reference, or for future use in an API-based fee calculation.
