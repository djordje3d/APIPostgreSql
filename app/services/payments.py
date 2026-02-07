from sqlalchemy import func
from app import models


def recalc_ticket_payment_status(db, ticket_id: int):
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        return None

    total_paid = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.ticket_id == ticket_id)
        .scalar()
    )

    # fee može biti null/0 dok nije exit
    fee = ticket.fee or 0

    if fee == 0:
        ticket.payment_status = "UNPAID"
    elif total_paid >= fee:
        ticket.payment_status = "PAID"
    elif total_paid > 0:
        ticket.payment_status = "PARTIALLY_PAID"
    else:
        ticket.payment_status = "UNPAID"

    return ticket


# When USE_API_PAYMENT_STATUS is true, the payments router calls this after create/update/delete payment.
# It’s kept for reference, or for future use in an API-based payment status calculation.
# When false, payment_status is expected to be updated by a DB trigger.
