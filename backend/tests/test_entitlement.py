"""Tests for entitlement utilities (Phase 2 Week 1)."""
from datetime import datetime, timedelta, timezone
import pytest

from app.utils.entitlement import has_pro_access, get_user_tier, requires_email_verification


def _user(entitlement="free", email_verified=False, pro_trial_ends_at=None, trial_used=False):
    """Minimal user-like object for entitlement helpers."""
    u = type("User", (), {})()
    u.entitlement = entitlement
    u.email_verified = email_verified
    u.pro_trial_ends_at = pro_trial_ends_at
    u.trial_used = trial_used
    return u


def test_has_pro_access_paid_pro():
    """Paid Pro user always has access."""
    user = _user(entitlement="pro")
    assert has_pro_access(user) is True


def test_has_pro_access_free():
    """Free user has no Pro access."""
    user = _user(entitlement="free", email_verified=False)
    assert has_pro_access(user) is False


def test_has_pro_access_trial_active():
    """Trial user with active trial has Pro access."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=7)
    user = _user(entitlement="free", email_verified=True, pro_trial_ends_at=end)
    assert has_pro_access(user) is True


def test_has_pro_access_trial_expired():
    """Trial user with expired trial has no Pro access."""
    now = datetime.now(timezone.utc)
    end = now - timedelta(days=1)
    user = _user(entitlement="free", email_verified=True, pro_trial_ends_at=end)
    assert has_pro_access(user) is False


def test_has_pro_access_unverified_no_trial():
    """Unverified free user has no Pro access."""
    user = _user(entitlement="free", email_verified=False)
    assert has_pro_access(user) is False


def test_get_user_tier_pro():
    """get_user_tier returns 'pro' for paid Pro."""
    user = _user(entitlement="pro")
    assert get_user_tier(user) == "pro"


def test_get_user_tier_free():
    """get_user_tier returns 'free' for free user."""
    user = _user(entitlement="free", email_verified=False)
    assert get_user_tier(user) == "free"


def test_get_user_tier_trial():
    """get_user_tier returns 'trial' for active trial."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=7)
    user = _user(entitlement="free", email_verified=True, pro_trial_ends_at=end)
    assert get_user_tier(user) == "trial"


def test_requires_email_verification_free_unverified():
    """Free unverified user requires email verification."""
    user = _user(entitlement="free", email_verified=False)
    assert requires_email_verification(user) is True


def test_requires_email_verification_pro():
    """Pro user does not require email verification."""
    user = _user(entitlement="pro", email_verified=False)
    assert requires_email_verification(user) is False


def test_requires_email_verification_free_verified():
    """Free verified user does not require email verification."""
    user = _user(entitlement="free", email_verified=True)
    assert requires_email_verification(user) is False
