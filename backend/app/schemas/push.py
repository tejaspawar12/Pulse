"""Push subscription and notification preference schemas."""
import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PushSubscriptionRegisterIn(BaseModel):
    """Body for registering a push token."""
    push_token: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., pattern="^(ios|android)$")


class PushSubscriptionOut(BaseModel):
    """Push subscription response."""
    id: UUID
    user_id: UUID
    platform: str
    is_active: bool

    model_config = {"from_attributes": True}


class NotificationPreferencesIn(BaseModel):
    """Body for updating notification preferences. Strict validation for reminder_time."""
    notifications_enabled: bool | None = None
    reminder_time: str | None = None  # "HH:MM", "" to clear, None = no change

    @field_validator("reminder_time")
    @classmethod
    def validate_reminder_time(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Invalid time format. Use HH:MM or '' to clear.")
        h, m = map(int, v.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Invalid time value. Use HH:MM in 24-hour range.")
        return v
