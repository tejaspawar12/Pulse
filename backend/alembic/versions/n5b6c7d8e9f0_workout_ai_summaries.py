"""workout_ai_summaries

Revision ID: n5b6c7d8e9f0
Revises: m4a5b6c7d8e9
Create Date: 2026-02-03

AI Summaries & Trends: per-workout cached LLM summary.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "n5b6c7d8e9f0"
down_revision: Union[str, None] = "m4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workout_ai_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workout_id", UUID(as_uuid=True), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workout_ai_summaries_workout_id", "workout_ai_summaries", ["workout_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_workout_ai_summaries_workout_id", table_name="workout_ai_summaries")
    op.drop_table("workout_ai_summaries")
