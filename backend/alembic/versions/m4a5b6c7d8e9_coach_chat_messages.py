"""coach_chat_messages

Revision ID: m4a5b6c7d8e9
Revises: l3a4b5c6d7e8
Create Date: 2026-02-03

Coach tab: multi-turn chat messages (user / assistant).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "m4a5b6c7d8e9"
down_revision: Union[str, None] = "l3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coach_chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_coach_chat_messages_user_id", "coach_chat_messages", ["user_id"])
    op.create_index("ix_coach_chat_messages_user_created", "coach_chat_messages", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_coach_chat_messages_user_created", table_name="coach_chat_messages")
    op.drop_index("ix_coach_chat_messages_user_id", table_name="coach_chat_messages")
    op.drop_table("coach_chat_messages")
