"""Tests for refresh token functionality (Phase 2 Week 1).

Requires test DB schema to include refresh_tokens and users entitlement columns.
Run: TEST_DATABASE_URL=postgresql://... alembic upgrade head  # then pytest
"""
import pytest

from app.services.auth_service import (
    create_refresh_token,
    refresh_access_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
)


def test_refresh_token_creation(db, test_user):
    """Test creating a refresh token."""
    token, raw = create_refresh_token(test_user.id, db)
    db.commit()

    assert token.user_id == test_user.id
    assert token.token_hash is not None
    assert raw is not None


def test_refresh_token_rotation(db, test_user):
    """Test that refresh rotates to new token."""
    _, raw = create_refresh_token(test_user.id, db)
    db.commit()

    result = refresh_access_token(raw, db)

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["refresh_token"] != raw


def test_refresh_token_reuse_detection(db, test_user):
    """Test that token reuse is detected."""
    _, raw = create_refresh_token(test_user.id, db)
    db.commit()

    refresh_access_token(raw, db)

    with pytest.raises(ValueError, match="reuse detected"):
        refresh_access_token(raw, db)


def test_revoke_refresh_token(db, test_user):
    """Test revoking a single refresh token."""
    _, raw = create_refresh_token(test_user.id, db)
    db.commit()

    revoked = revoke_refresh_token(raw, db)
    assert revoked is True

    with pytest.raises(ValueError, match="Token revoked"):
        refresh_access_token(raw, db)


def test_revoke_all_user_tokens(db, test_user):
    """Test revoking all tokens for a user."""
    _, raw1 = create_refresh_token(test_user.id, db)
    db.commit()
    _, raw2 = create_refresh_token(test_user.id, db)
    db.commit()

    count = revoke_all_user_tokens(test_user.id, db)
    assert count >= 2

    with pytest.raises(ValueError, match="Token revoked"):
        refresh_access_token(raw1, db)
    with pytest.raises(ValueError, match="Token revoked"):
        refresh_access_token(raw2, db)
