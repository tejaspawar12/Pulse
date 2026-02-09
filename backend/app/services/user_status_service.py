"""
User status service for business logic.
Handles user status queries including active workout, today's status, and last 30 days.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, date
from uuid import UUID
from typing import Optional

from app.models.user import User
from app.models.workout import Workout
# Import ExerciseLibrary to ensure SQLAlchemy can resolve relationships
from app.models.exercise import ExerciseLibrary
from app.schemas.user import UserStatusOut, DailyStatus
from app.schemas.workout import ActiveWorkoutSummary
from app.utils.enums import LifecycleStatus, CompletionStatus
from app.utils.helpers import to_bool


class UserStatusService:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_active_workout_summary(self, user_id: UUID, user_timezone: str) -> Optional[ActiveWorkoutSummary]:
        """
        Get active draft workout summary.
        
        Uses SQL counts (not Python loops) for performance.
        Computes date in single query.
        
        Args:
            user_id: User ID
            user_timezone: User timezone (e.g., "Asia/Kolkata")
        
        Returns:
            ActiveWorkoutSummary or None if no active workout
        """
        # Single SQL query: get workout + date + counts
        # Use timezone() function with string formatting for timezone name
        # ORDER BY start_time DESC ensures deterministic selection (latest draft)
        query = text(f"""
            SELECT 
                w.id,
                w.name,
                w.start_time,
                DATE(timezone('{user_timezone}', w.start_time)) as workout_date,
                COUNT(DISTINCT we.id) as exercise_count,
                COUNT(ws.id) as set_count
            FROM workouts w
            LEFT JOIN workout_exercises we ON we.workout_id = w.id
            LEFT JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'draft'
            GROUP BY w.id, w.name, w.start_time
            ORDER BY w.start_time DESC
            LIMIT 1
        """)
        
        result = self.db.execute(
            query,
            {"user_id": str(user_id)}
        ).first()
        
        if not result:
            return None
        
        return ActiveWorkoutSummary(
            id=result.id,
            date=result.workout_date,
            name=result.name,
            exercise_count=result.exercise_count or 0,
            set_count=result.set_count or 0,
            start_time=result.start_time
        )
    
    def _get_today_date(self, user_timezone: str) -> date:
        """
        Get today's date in user timezone.
        
        Args:
            user_timezone: User timezone (e.g., "Asia/Kolkata")
        
        Returns:
            date: Today's date in user timezone
        """
        # Compute "today" using user timezone (LOCKED)
        # Use timezone() function with proper quoting for timezone name
        # NOTE: Requires start_time column to be TIMESTAMPTZ (verified in Step 2.3)
        try:
            # PostgreSQL timezone() function: timezone(zone, timestamp)
            # Use proper parameter binding - timezone name must be a string literal in SQL
            # We need to use string formatting for the timezone name (it's validated from user.timezone)
            # But use parameter binding for safety where possible
            today_query = text(f"""
                SELECT DATE(timezone('{user_timezone}', now())) as today
            """)
            result = self.db.execute(today_query)
            today_date = result.scalar()
            return today_date
        except Exception as e:
            # Fallback to UTC if timezone conversion fails (no PII in logs — Week 8)
            import logging
            logging.getLogger(__name__).warning("Timezone conversion failed, falling back to UTC: %s", type(e).__name__)
            from datetime import timezone as tz
            today_date = datetime.now(tz.utc).date()
            return today_date
    
    def _get_worked_out_dates(self, user_id: UUID, user_timezone: str, days_back: int = 45) -> set[date]:
        """
        Get set of dates when user worked out (in user timezone).
        
        Uses single SQL query (not N+1) for performance.
        
        Args:
            user_id: User ID
            user_timezone: User timezone (e.g., "Asia/Kolkata")
            days_back: Number of days to look back (default 45 to account for timezone shifts)
        
        Returns:
            set[date]: Set of dates when user worked out
        """
        # Single SQL query: get distinct dates in user timezone
        # Use timezone() function with string formatting for timezone name
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        query = text(f"""
            SELECT DISTINCT DATE(timezone('{user_timezone}', start_time)) AS workout_date
            FROM workouts
            WHERE user_id = :user_id
              AND lifecycle_status = 'finalized'
              AND completion_status IN ('completed', 'partial')
              AND start_time >= :cutoff
        """)
        
        rows = self.db.execute(
            query,
            {
                "user_id": str(user_id),
                "cutoff": cutoff
            }
        ).all()
        
        # Convert to set of dates
        worked_out_dates = {row.workout_date for row in rows}
        return worked_out_dates
    
    def get_user_status(self, user_id: UUID) -> UserStatusOut:
        """
        Get user status: active workout, today's status, last 30 days.
        
        Logic:
        1. Get user (for timezone)
        2. Get active workout summary (if exists)
        3. Get today's date in user timezone
        4. Get worked out dates from finalized workouts
        5. Build last 30 days list
        6. Check if worked out today
        
        Args:
            user_id: User ID
        
        Returns:
            UserStatusOut: User status with active workout, today status, last 30 days
        """
        try:
            # Get user (for timezone)
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            # Validate and set timezone (must be a valid PostgreSQL timezone name)
            user_timezone = user.timezone or "Asia/Kolkata"  # Default fallback

            # Sanitize timezone name to prevent SQL injection (basic check)
            import re
            if not re.match(r"^[A-Za-z0-9_/+-]+$", user_timezone):
                user_timezone = "UTC"

            # Get active workout summary
            active_workout_summary = self._get_active_workout_summary(user_id, user_timezone)

            # Get today's date in user timezone
            today_date = self._get_today_date(user_timezone)

            # Get worked out dates
            worked_out_dates = self._get_worked_out_dates(user_id, user_timezone, days_back=45)

            # Build last 30 days list (ordered: oldest → newest, LOCKED)
            last_30_days = []
            for i in range(29, -1, -1):  # Start from 29 days ago, go to today
                check_date = today_date - timedelta(days=i)
                worked_out = check_date in worked_out_dates
                normalized_bool = to_bool(worked_out)
                last_30_days.append(DailyStatus(
                    date=check_date,
                    worked_out=normalized_bool
                ))

            # Check if worked out today - ensure proper bool type
            today_worked_out_raw = today_date in worked_out_dates
            today_worked_out = to_bool(today_worked_out_raw)

            result = UserStatusOut(
                active_workout=active_workout_summary,
                today_worked_out=today_worked_out,
                last_30_days=last_30_days
            )
            return result
        except ValueError:
            raise
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("get_user_status failed")
            raise ValueError("Failed to get user status") from e
