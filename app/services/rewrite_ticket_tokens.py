from app.db import SessionLocal
from app import models
from app.services.tokens import generate_unique_ticket_token

db = SessionLocal()

try:
    tickets = db.query(models.Ticket).order_by(models.Ticket.id).all()

    for ticket in tickets:
        old_token = ticket.ticket_token
        new_token = generate_unique_ticket_token(db, ticket.garage_id)  # type: ignore[arg-type]
        setattr(ticket, "ticket_token", new_token)
        db.flush()  # so next generate_unique_ticket_token sees this token
        print(f"{ticket.id}: {old_token} -> {new_token}")

    db.commit()
    print("All ticket tokens updated successfully.")

except Exception as e:
    db.rollback()
    print("Error:", e)
    raise

finally:
    db.close()
