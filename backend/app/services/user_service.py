"""
User service for user profile and settings management.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
import pytz

from app.models.user import User
from app.schemas.user import UpdateUserIn

# ✅ Load timezone list once at module level (performance optimization)
# Avoids loading pytz.all_timezones on every request
VALID_TIMEZONES = set(pytz.all_timezones)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def update_user_settings(
        self,
        user_id: UUID,
        data: UpdateUserIn
    ) -> User:
        """
        Update user settings.
        
        Args:
            user_id: User UUID
            data: Update data (units, timezone, default_rest_timer_seconds)
        
        Returns:
            User: Updated user
        
        Raises:
            HTTPException: If user not found or validation fails
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        # ✅ Units: Enum ensures only kg/lb, no need to validate again
        # ⚠️ CRITICAL: Ensure User.units column is String type and stores "kg"/"lb"
        if data.units is not None:
            user.units = data.units.value  # Enum value (str) - stores "kg" or "lb"
        
        if data.timezone is not None:
            # ⚠️ CRITICAL: Validate timezone to prevent Postgres errors
            # Invalid timezone strings can break Postgres AT TIME ZONE queries
            # ✅ Use pre-loaded set for fast lookup (performance)
            if data.timezone not in VALID_TIMEZONES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid timezone: {data.timezone}. Must be a valid IANA timezone."
                )
            user.timezone = data.timezone
        
        # ✅ Rest timer: Schema validation (ge=0) already ensures non-negative
        if data.default_rest_timer_seconds is not None:
            user.default_rest_timer_seconds = data.default_rest_timer_seconds

        # Body / personal (for coach, plan, predictions); allow null to clear
        dump = data.model_dump(exclude_unset=True)
        if "weight_kg" in dump:
            user.weight_kg = data.weight_kg
        if "height_cm" in dump:
            user.height_cm = data.height_cm
        if "date_of_birth" in dump:
            user.date_of_birth = data.date_of_birth
        if "gender" in dump:
            user.gender = data.gender
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
