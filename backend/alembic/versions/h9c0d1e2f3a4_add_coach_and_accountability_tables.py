"""add_coach_and_accountability_tables

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-02-01

Phase 2 Week 5: Coach and accountability tables.
Unique constraints: (user_id, message_date), (user_id, usage_date), (user_id, commitment_date), (user_id, metrics_date).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "h9c0d1e2f3a4"
down_revision: Union[str, None] = "g8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_coach_profiles
    op.create_table(
        "user_coach_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("primary_goal", sa.String(50), nullable=True),
        sa.Column("experience_level", sa.String(20), nullable=True),
        sa.Column("target_days_per_week", sa.Integer(), nullable=True),
        sa.Column("target_session_minutes", sa.Integer(), nullable=True),
        sa.Column("available_equipment", ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_workout_time", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_user_coach_profiles_user_id", "user_coach_profiles", ["user_id"], unique=True)

    # 2. user_behavior_metrics — Unique (user_id, metrics_date)
    op.create_table(
        "user_behavior_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metrics_date", sa.Date(), nullable=False),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("dropout_risk", sa.String(20), nullable=True),
        sa.Column("burnout_risk", sa.String(20), nullable=True),
        sa.Column("momentum_trend", sa.String(20), nullable=True),
        sa.Column("adherence_type", sa.String(30), nullable=True),
        sa.Column("workouts_last_7_days", sa.Integer(), nullable=True),
        sa.Column("workouts_last_14_days", sa.Integer(), nullable=True),
        sa.Column("avg_session_duration_minutes", sa.Float(), nullable=True),
        sa.Column("total_volume_last_7_days", sa.Float(), nullable=True),
        sa.Column("volume_delta_vs_prev_week", sa.Float(), nullable=True),
        sa.Column("max_gap_days", sa.Integer(), nullable=True),
        sa.Column("common_skip_day", sa.String(10), nullable=True),
        sa.Column("primary_training_mistake_key", sa.String(50), nullable=True),
        sa.Column("primary_training_mistake_label", sa.String(255), nullable=True),
        sa.Column("weekly_focus_key", sa.String(50), nullable=True),
        sa.Column("weekly_focus_label", sa.String(255), nullable=True),
        sa.Column("reasons", JSONB(), nullable=True),
        sa.UniqueConstraint("user_id", "metrics_date", name="uq_user_behavior_metrics_user_date"),
    )
    op.create_index("ix_behavior_metrics_user_computed", "user_behavior_metrics", ["user_id", "computed_at"])
    op.create_index("ix_user_behavior_metrics_user_id", "user_behavior_metrics", ["user_id"])

    # 3. coach_messages — Unique (user_id, message_date)
    op.create_table(
        "coach_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_date", sa.Date(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "message_date", name="uq_coach_message_user_date"),
    )
    op.create_index("ix_coach_messages_user_date", "coach_messages", ["user_id", "message_date"])
    op.create_index("ix_coach_messages_user_id", "coach_messages", ["user_id"])

    # 4. llm_usage_daily — Unique (user_id, usage_date)
    op.create_table(
        "llm_usage_daily",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("coach_calls", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("report_calls", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("plan_calls", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("summary_calls", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_llm_usage_user_date"),
    )
    op.create_index("ix_llm_usage_user_date", "llm_usage_daily", ["user_id", "usage_date"])
    op.create_index("ix_llm_usage_daily_user_id", "llm_usage_daily", ["user_id"])

    # 5. daily_commitments — Unique (user_id, commitment_date); status: yes | no | rescheduled
    op.create_table(
        "daily_commitments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commitment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=True),  # yes, no, rescheduled
        sa.Column("expected_time", sa.Time(), nullable=True),
        sa.Column("expected_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workout_id", UUID(as_uuid=True), sa.ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("follow_up_sent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("escalation_level", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "commitment_date", name="uq_user_commitment_date"),
    )
    op.create_index("ix_commitments_user_date", "daily_commitments", ["user_id", "commitment_date"])
    op.create_index("ix_daily_commitments_user_id", "daily_commitments", ["user_id"])

    # 6. accountability_events
    op.create_table(
        "accountability_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commitment_id", UUID(as_uuid=True), sa.ForeignKey("daily_commitments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("event_data", JSONB(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_accountability_events_user_id", "accountability_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_accountability_events_user_id", table_name="accountability_events")
    op.drop_table("accountability_events")

    op.drop_index("ix_daily_commitments_user_id", table_name="daily_commitments")
    op.drop_index("ix_commitments_user_date", table_name="daily_commitments")
    op.drop_table("daily_commitments")

    op.drop_index("ix_llm_usage_daily_user_id", table_name="llm_usage_daily")
    op.drop_index("ix_llm_usage_user_date", table_name="llm_usage_daily")
    op.drop_table("llm_usage_daily")

    op.drop_index("ix_coach_messages_user_id", table_name="coach_messages")
    op.drop_index("ix_coach_messages_user_date", table_name="coach_messages")
    op.drop_table("coach_messages")

    op.drop_index("ix_user_behavior_metrics_user_id", table_name="user_behavior_metrics")
    op.drop_index("ix_behavior_metrics_user_computed", table_name="user_behavior_metrics")
    op.drop_table("user_behavior_metrics")

    op.drop_index("ix_user_coach_profiles_user_id", table_name="user_coach_profiles")
    op.drop_table("user_coach_profiles")
