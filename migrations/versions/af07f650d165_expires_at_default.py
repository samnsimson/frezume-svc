"""expires at default

Revision ID: af07f650d165
Revises: c7885811b230
Create Date: 2025-12-25 01:00:19.149527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'af07f650d165'
down_revision: Union[str, Sequence[str], None] = 'c7885811b230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update NULL values to default (30 days from now) before setting NOT NULL
    # Using PostgreSQL's NOW() + INTERVAL for reliability
    op.execute("UPDATE session SET expires_at = NOW() AT TIME ZONE 'UTC' + INTERVAL '30 days' WHERE expires_at IS NULL")
    op.execute("UPDATE verification SET expires_at = NOW() AT TIME ZONE 'UTC' + INTERVAL '30 days' WHERE expires_at IS NULL")

    # Now alter columns to NOT NULL
    op.alter_column('session', 'expires_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    nullable=False)
    op.alter_column('verification', 'expires_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('verification', 'expires_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    nullable=True)
    op.alter_column('session', 'expires_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    nullable=True)
