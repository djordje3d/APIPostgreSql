"""change_ticket_token_to_base32_format

Revision ID: 147183f70972
Revises: 8a34a74bbbcc
Create Date: 2026-03-16 15:34:07.691293
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "147183f70972"
down_revision: Union[str, Sequence[str], None] = "8a34a74bbbcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update existing ticket_token values to Base32-like format without dashes.

    Old format:
        GAR{garage_id}-XXXXXXXX

    New format:
        G{garage_id}{random_part}

    Example:
        G3K9F2A8
    """

    op.execute(
        """
        UPDATE tickets
        SET ticket_token =
            'G' || garage_id::text ||
            (
                SELECT string_agg(
                    substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789',
                           1 + floor(random() * 32)::int,
                           1),
                    ''
                )
                FROM generate_series(1, 6)
            )
        """
    )


def downgrade() -> None:
    """
    Revert token format back to GAR{garage_id}-XXXXXXXX style.
    """

    op.execute(
        """
        UPDATE tickets
        SET ticket_token =
            'GAR' || garage_id::text || '-' ||
            upper(substring(md5(random()::text || clock_timestamp()::text), 1, 8))
        """
    )