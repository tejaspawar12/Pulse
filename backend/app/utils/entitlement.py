"""Entitlement utilities for premium access control."""
from datetime import datetime, timezone


def has_pro_access(user, now: datetime | None = None) -> bool:
    """
    Single source of truth for Pro access.
    Every endpoint that gates premium features MUST use this function.

    Rules:
    - Paid Pro users: ALWAYS have access (even if email not verified)
    - Trial users: MUST have verified email AND active trial period
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if getattr(user, "entitlement", None) == "pro":
        return True

    if (
        getattr(user, "email_verified", False)
        and getattr(user, "pro_trial_ends_at", None)
        and now < user.pro_trial_ends_at
    ):
        return True

    return False


def requires_email_verification(user) -> bool:
    """Check if user needs to verify email before accessing features."""
    if getattr(user, "entitlement", None) == "pro":
        return False
    return not getattr(user, "email_verified", False)


def get_user_tier(user) -> str:
    """Get user's current tier for display purposes."""
    if getattr(user, "entitlement", None) == "pro":
        return "pro"
    if getattr(user, "email_verified", False) and getattr(user, "pro_trial_ends_at", None):
        if datetime.now(timezone.utc) < user.pro_trial_ends_at:
            return "trial"
    return "free"
