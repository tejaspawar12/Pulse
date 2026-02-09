"""coach_message_source_and_debug_columns

Revision ID: i0d1e2f3a4b5
Revises: h9c0d1e2f3a4
Create Date: 2026-02-02

Phase 2 Week 5 Day 3: Add source, generated_at, model_id, ai_lite_used to coach_messages.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "i0d1e2f3a4b5"
down_revision: Union[str, None] = "h9c0d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("coach_messages", sa.Column("source", sa.String(20), nullable=True))
    op.add_column("coach_messages", sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("coach_messages", sa.Column("model_id", sa.String(128), nullable=True))
    op.add_column("coach_messages", sa.Column("ai_lite_used", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    # Backfill existing rows so source is set; then make NOT NULL
    op.execute("UPDATE coach_messages SET source = 'ai' WHERE source IS NULL")
    op.alter_column(
        "coach_messages",
        "source",
        existing_type=sa.String(20),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("coach_messages", "ai_lite_used")
    op.drop_column("coach_messages", "model_id")
    op.drop_column("coach_messages", "generated_at")
    op.drop_column("coach_messages", "source")
