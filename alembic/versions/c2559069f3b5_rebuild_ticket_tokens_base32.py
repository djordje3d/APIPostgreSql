"""rebuild_ticket_tokens_base32

Revision ID: c2559069f3b5
Revises: 147183f70972
Create Date: 2026-03-16 19:32:57.181147

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2559069f3b5"
down_revision: Union[str, Sequence[str], None] = "147183f70972"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.execute(
        """
        UPDATE tickets
        SET ticket_token =
            'GAR' || garage_id::text || '-' ||
            upper(substring(md5(random()::text || clock_timestamp()::text), 1, 8))
        """
    )
