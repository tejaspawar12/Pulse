"""user body fields (weight, height, dob, gender)

Revision ID: o6c7d8e9f0a1
Revises: n5b6c7d8e9f0
Create Date: 2026-02-08

Add body/personal fields to users for coach, plan, and predictions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "o6c7d8e9f0a1"
down_revision: Union[str, None] = "n5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("weight_kg", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("height_cm", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "gender")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "height_cm")
    op.drop_column("users", "weight_kg")
