"""
Application configuration. Use environment variables to choose whether
fee calculation and payment status updates are done in the API or by the DB.

- When using a database that has triggers: set both to false (default).
- When using a database without those triggers: set both to true so the API
  computes ticket fee on exit and updates ticket payment_status after payments.
"""
import os


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "false" if not default else "true").lower()
    return value in ("true", "1", "yes")


# If True, API computes ticket fee and sets ticket_state to CLOSED on exit.
# If False, API only sets exit_time; fee/state expected from a DB trigger.
USE_API_FEE_CALCULATION: bool = _env_bool("USE_API_FEE_CALCULATION", default=False)

# If True, API recalculates ticket.payment_status after create/update/delete payment.
# If False, payment_status is expected to be updated by a DB trigger.
USE_API_PAYMENT_STATUS: bool = _env_bool("USE_API_PAYMENT_STATUS", default=False)
