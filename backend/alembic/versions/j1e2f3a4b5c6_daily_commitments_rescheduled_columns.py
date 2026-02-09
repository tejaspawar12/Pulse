"""daily_commitments_rescheduled_columns

Revision ID: j1e2f3a4b5c6
Revises: i0d1e2f3a4b5
Create Date: 2026-02-02

Phase 2 Week 5 Day 4: Add rescheduled_to_date, rescheduled_to_time to daily_commitments.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "j1e2f3a4b5c6"
down_revision: Union[str, None] = "i0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("daily_commitments", sa.Column("rescheduled_to_date", sa.Date(), nullable=True))
    op.add_column("daily_commitments", sa.Column("rescheduled_to_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("daily_commitments", "rescheduled_to_time")
    op.drop_column("daily_commitments", "rescheduled_to_date")
