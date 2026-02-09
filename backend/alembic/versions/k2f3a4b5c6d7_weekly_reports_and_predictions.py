"""weekly_reports_and_predictions

Revision ID: k2f3a4b5c6d7
Revises: j1e2f3a4b5c6
Create Date: 2026-02-03

Phase 2 Week 6: weekly_training_reports and transformation_predictions tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "k2f3a4b5c6d7"
down_revision: Union[str, None] = "j1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. weekly_training_reports — Unique (user_id, week_start)
    op.create_table(
        "weekly_training_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("workouts_count", sa.Integer(), nullable=True),
        sa.Column("total_volume_kg", sa.Float(), nullable=True),
        sa.Column("volume_delta_pct", sa.Float(), nullable=True),
        sa.Column("prs_hit", sa.Integer(), nullable=True),
        sa.Column("avg_session_duration", sa.Float(), nullable=True),
        sa.Column("primary_training_mistake_key", sa.String(50), nullable=True),
        sa.Column("primary_training_mistake_label", sa.String(255), nullable=True),
        sa.Column("weekly_focus_key", sa.String(50), nullable=True),
        sa.Column("weekly_focus_label", sa.String(255), nullable=True),
        sa.Column("positive_signal_key", sa.String(50), nullable=True),
        sa.Column("positive_signal_label", sa.String(255), nullable=True),
        sa.Column("positive_signal_reason", sa.String(255), nullable=True),
        sa.Column("reasons", JSONB(), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("narrative_source", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("narrative_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "week_start", name="uq_weekly_report_user_week"),
    )
    op.create_index("ix_weekly_training_reports_user_id", "weekly_training_reports", ["user_id"])
    op.create_index("ix_weekly_training_reports_user_week", "weekly_training_reports", ["user_id", "week_start"])

    # 2. transformation_predictions — no unique constraint (history)
    op.create_table(
        "transformation_predictions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("strength_gain_weeks", sa.Integer(), nullable=True),
        sa.Column("visible_change_weeks", sa.Integer(), nullable=True),
        sa.Column("next_milestone", sa.String(100), nullable=True),
        sa.Column("next_milestone_weeks", sa.Integer(), nullable=True),
        sa.Column("weeks_delta", sa.Integer(), nullable=True),
        sa.Column("delta_reason", sa.String(255), nullable=True),
        sa.Column("current_consistency_score", sa.Float(), nullable=True),
        sa.Column("current_workouts_per_week", sa.Float(), nullable=True),
    )
    op.create_index("ix_transformation_predictions_user_id", "transformation_predictions", ["user_id"])
    op.create_index("ix_transformation_predictions_user_computed", "transformation_predictions", ["user_id", "computed_at"])


def downgrade() -> None:
    op.drop_index("ix_transformation_predictions_user_computed", table_name="transformation_predictions")
    op.drop_index("ix_transformation_predictions_user_id", table_name="transformation_predictions")
    op.drop_table("transformation_predictions")
    op.drop_index("ix_weekly_training_reports_user_week", table_name="weekly_training_reports")
    op.drop_index("ix_weekly_training_reports_user_id", table_name="weekly_training_reports")
    op.drop_table("weekly_training_reports")
