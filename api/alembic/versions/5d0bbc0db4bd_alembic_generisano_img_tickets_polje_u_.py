"""Alembic generisano img tickets polje u bazi

Revision ID: 5d0bbc0db4bd
Revises: 31c331922e6b
Create Date: 2026-03-13 00:26:20.962667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d0bbc0db4bd'
down_revision: Union[str, Sequence[str], None] = '31c331922e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
