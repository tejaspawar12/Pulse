"""transformation_prediction primary_goal

Revision ID: p7d8e9f0a1b2
Revises: o6c7d8e9f0a1
Create Date: 2026-02-08

Add primary_goal to transformation_predictions for goal-based timeline.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p7d8e9f0a1b2"
down_revision: Union[str, None] = "o6c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transformation_predictions",
        sa.Column("primary_goal", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transformation_predictions", "primary_goal")
