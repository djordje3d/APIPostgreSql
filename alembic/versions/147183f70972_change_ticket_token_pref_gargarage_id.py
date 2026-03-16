"""change_ticket_token_pref_GARgarage_id

Revision ID: 147183f70972
Revises: 8a34a74bbbcc
Create Date: 2026-03-16 15:34:07.691293

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "147183f70972"
down_revision: Union[str, Sequence[str], None] = "8a34a74bbbcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update existing ticket_token values to include garage_id.
    Old format: GAR-XXXXXXXX
    New format: GAR{garage_id}-XXXXXXXX
    """

    op.execute(
        """
        UPDATE tickets
        SET ticket_token =
            'GAR' || garage_id::text || '-' ||
            upper(substring(md5(random()::text || clock_timestamp()::text), 1, 8))
        """
    )


def downgrade() -> None:
    """
    Revert token format back to GAR-XXXXXXXX.
    """

    op.execute(
        """
        UPDATE tickets
        SET ticket_token =
            'GAR-' ||
            upper(substring(md5(random()::text || clock_timestamp()::text), 1, 8))
        """
    )
