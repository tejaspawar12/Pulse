"""plan_tables

Revision ID: l3a4b5c6d7e8
Revises: k2f3a4b5c6d7
Create Date: 2026-02-03

Phase 2 Week 7: training_plans and weekly_plan_adjustments tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "l3a4b5c6d7e8"
down_revision: Union[str, None] = "k2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. training_plans — one per user
    op.create_table(
        "training_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=True),
        sa.Column("session_duration_target", sa.Integer(), nullable=True),
        sa.Column("split_type", sa.String(30), nullable=True),
        sa.Column("volume_multiplier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("progression_type", sa.String(30), nullable=True),
        sa.Column("auto_adjust_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deload_week_frequency", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_training_plans_user_id", "training_plans", ["user_id"], unique=True)

    # 2. weekly_plan_adjustments — unique (plan_id, week_start), index (user_id, week_start desc)
    op.create_table(
        "weekly_plan_adjustments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("previous_days_per_week", sa.Integer(), nullable=True),
        sa.Column("new_days_per_week", sa.Integer(), nullable=True),
        sa.Column("previous_volume_multiplier", sa.Float(), nullable=True),
        sa.Column("new_volume_multiplier", sa.Float(), nullable=True),
        sa.Column("is_deload", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("trigger_reason", sa.String(50), nullable=True),
        sa.Column("explanation_bullets", JSONB(), nullable=True),
        sa.Column("metrics_snapshot", JSONB(), nullable=True),
        sa.Column("explanation_title", sa.String(80), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("plan_id", "week_start", name="uq_weekly_plan_adj_plan_week"),
    )
    op.create_index("ix_weekly_plan_adjustments_user_id", "weekly_plan_adjustments", ["user_id"])
    op.create_index("ix_weekly_plan_adjustments_plan_id", "weekly_plan_adjustments", ["plan_id"])
    op.create_index(
        "idx_weekly_adj_user_weekstart",
        "weekly_plan_adjustments",
        ["user_id", "week_start"],
        postgresql_ops={"week_start": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("idx_weekly_adj_user_weekstart", table_name="weekly_plan_adjustments")
    op.drop_index("ix_weekly_plan_adjustments_plan_id", table_name="weekly_plan_adjustments")
    op.drop_index("ix_weekly_plan_adjustments_user_id", table_name="weekly_plan_adjustments")
    op.drop_table("weekly_plan_adjustments")
    op.drop_index("ix_training_plans_user_id", table_name="training_plans")
    op.drop_table("training_plans")
