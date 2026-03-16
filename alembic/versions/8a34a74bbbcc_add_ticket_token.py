"""add_ticket_token

Revision ID: 8a34a74bbbcc
Revises: 5d0bbc0db4bd
Create Date: 2026-03-16 13:02:33.572916

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8a34a74bbbcc"
down_revision: Union[str, Sequence[str], None] = "5d0bbc0db4bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "tickets",
        sa.Column("ticket_token", sa.String(length=32), nullable=True),
    )

    op.execute(
        """
        UPDATE tickets
        SET ticket_token = 'GAR-' || substring(md5(random()::text), 1, 8)
        WHERE ticket_token IS NULL
    """
    )

    op.alter_column("tickets", "ticket_token", nullable=False)

    op.create_unique_constraint(
        "uq_tickets_ticket_token",
        "tickets",
        ["ticket_token"],
    )


def downgrade():
    op.drop_constraint("uq_tickets_ticket_token", "tickets", type_="unique")
    op.drop_column("tickets", "ticket_token")
