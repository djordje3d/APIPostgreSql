"""add_ticket_image_url

Revision ID: 31c331922e6b
Revises:
Create Date: 2026-03-13 00:10:13.019565

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "31c331922e6b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tickets", sa.Column("image_url", sa.String(512), nullable=True)  # table name
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tickets", "image_url")
