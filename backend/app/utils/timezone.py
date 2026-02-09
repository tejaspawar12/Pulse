"""Timezone utilities for user-local date/time operations."""
from datetime import date, datetime, time

import pytz


def user_now(tz_name: str | None) -> datetime:
    """Get current datetime in user's timezone."""
    timezone_obj = pytz.timezone(tz_name or "UTC")
    return datetime.now(timezone_obj)


def user_today(tz_name: str | None) -> date:
    """Get today's date in user's timezone."""
    return user_now(tz_name).date()


def user_local_time(tz_name: str | None) -> time:
    """Get current time in user's timezone."""
    return user_now(tz_name).time()


def is_in_time_window(
    tz_name: str | None,
    start_hour: int,
    end_hour: int,
    target_weekday: int | None = None,
) -> bool:
    """
    Check if current user-local time is within a window.

    Args:
        tz_name: User's timezone (e.g., "America/New_York")
        start_hour: Window start hour (0-23)
        end_hour: Window end hour (0-23, exclusive)
        target_weekday: Optional weekday (0=Monday, 6=Sunday)

    Example: is_in_time_window(tz, 3, 4, 0) = Monday 3:00-3:59 AM
    """
    now = user_now(tz_name)

    if target_weekday is not None and now.weekday() != target_weekday:
        return False

    return start_hour <= now.hour < end_hour
