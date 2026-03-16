import secrets
from sqlalchemy.orm import Session
from app import models

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# Generiši token za ovu garažu. Token mora da se generiše pre dodavanja u bazu.
# Token je u formatu: G{garage_id}{random_part}
def generate_ticket_token(garage_id: int) -> str:
    random_part = "".join(secrets.choice(ALPHABET) for _ in range(6))
    return f"G{garage_id}{random_part}"


def generate_unique_ticket_token(db: Session, garage_id: int) -> str:
    while True:
        token = generate_ticket_token(garage_id)
        exists = (
            db.query(models.Ticket).filter(models.Ticket.ticket_token == token).first()
        )
        if not exists:
            return token
