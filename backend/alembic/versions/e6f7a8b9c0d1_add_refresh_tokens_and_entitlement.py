"""add_refresh_tokens_and_entitlement

Revision ID: e6f7a8b9c0d1
Revises: a1b2c3d4e5f6
Create Date: 2026-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('token_family_id', UUID(as_uuid=True), nullable=False),
        sa.Column('replaced_by_id', UUID(as_uuid=True), sa.ForeignKey('refresh_tokens.id', ondelete='CASCADE'), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('device_info', sa.String(255), nullable=True),
        sa.Column('ip_hash', sa.String(64), nullable=True),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_user_expires', 'refresh_tokens', ['user_id', 'expires_at'])
    op.create_index('ix_refresh_tokens_family', 'refresh_tokens', ['token_family_id'])
    op.create_index('ix_refresh_tokens_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_revoked', 'refresh_tokens', ['revoked_at'])

    # 2. Extend users table with entitlement columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('entitlement', sa.String(20), server_default=sa.text("'free'"), nullable=False))
    op.add_column('users', sa.Column('pro_trial_ends_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('trial_used', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'trial_used')
    op.drop_column('users', 'pro_trial_ends_at')
    op.drop_column('users', 'entitlement')
    op.drop_column('users', 'email_verified')

    op.drop_index('ix_refresh_tokens_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_family', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_expires', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
