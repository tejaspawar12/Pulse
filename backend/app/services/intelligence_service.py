"""
Intelligence service: compute behavior metrics from workouts + coach profile (rules-only, no LLM).
Phase 2 Week 5 Day 2.
"""
import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.dialects.postgresql import insert

from app.models.user import User
from app.models.user_coach_profile import UserCoachProfile
from app.models.user_behavior_metrics import UserBehaviorMetrics
from app.utils.timezone import user_today


# Default profile when user has no coach profile
DEFAULT_TARGET_DAYS_PER_WEEK = 3
DEFAULT_TARGET_SESSION_MINUTES = 45

# Mistake key -> (focus_key, focus_label)
MISTAKE_TO_FOCUS = {
    "inconsistent_training_days": ("hit_target_days", "Hit your target workouts this week"),
    "volume_drop": ("add_extra_set", "Add 1 extra set per exercise"),
    "no_progression_21_days": ("progression_check", "Try adding weight or reps on your main lifts"),
    "overtraining_signals": ("recovery_focus", "Prioritize recovery and sleep"),
    "sessions_too_short": ("lengthen_sessions", "Aim for at least {target} minutes per session"),
}


def _sanitize_timezone(tz: str) -> str:
    """Allow only safe timezone chars (alphanumeric, underscore, slash, plus, minus)."""
    if not tz or not re.match(r"^[A-Za-z0-9_/+-]+$", tz):
        return "UTC"
    return tz


class IntelligenceService:
    """
    Computes UserBehaviorMetrics from workouts and coach profile.
    Singleton: create one instance and reuse (e.g. in coach_service).
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_metrics(self, user_id: UUID, metrics_date: Optional[date] = None) -> UserBehaviorMetrics:
        """
        Compute behavior metrics for the given user and date.
        Loads coach profile (or defaults), recent finalized workouts, applies mistake rules,
        focus mapping, builds reasons, and upserts UserBehaviorMetrics.
        Caller is responsible for commit.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user_tz = _sanitize_timezone(user.timezone or "Asia/Kolkata")
        today = metrics_date if metrics_date is not None else user_today(user_tz)

        # Load coach profile or use defaults
        profile = self.db.query(UserCoachProfile).filter(UserCoachProfile.user_id == user_id).first()
        target_days = (profile.target_days_per_week if profile else None) or DEFAULT_TARGET_DAYS_PER_WEEK
        target_minutes = (profile.target_session_minutes if profile else None) or DEFAULT_TARGET_SESSION_MINUTES

        # Workout-derived data (last 30 days in user TZ)
        worked_dates = self._get_worked_out_dates(user_id, user_tz, days_back=30)
        workouts_7 = sum(1 for d in worked_dates if (today - d).days < 7)
        workouts_14 = sum(1 for d in worked_dates if (today - d).days < 14)

        volume_7, volume_prev_7, avg_duration_7 = self._get_volume_and_duration(
            user_id, user_tz, today
        )
        volume_delta_pct = self._volume_delta_pct(volume_7, volume_prev_7)

        max_gap = self._max_gap_days(worked_dates, today)
        common_skip = self._common_skip_day(worked_dates, today, days_back=30)

        # Consistency score 0–100 (how well they hit target over 2 weeks)
        consistency_score = self._consistency_score(workouts_14, target_days)

        # Risks and trends
        dropout_risk = self._dropout_risk(workouts_14, max_gap)
        burnout_risk = self._burnout_risk(workouts_14, avg_duration_7, target_minutes)
        momentum_trend = self._momentum_trend(volume_delta_pct)
        adherence_type = self._adherence_type(worked_dates, today, max_gap)

        # Mistake detection (first match wins)
        mistake_key, mistake_label = self._detect_mistake(
            workouts_14=workouts_14,
            target_days=target_days,
            max_gap=max_gap,
            volume_7=volume_7,
            volume_prev_7=volume_prev_7,
            avg_duration_7=avg_duration_7,
            target_minutes=target_minutes,
            burnout_risk=burnout_risk,
        )
        focus_key, focus_label = self._mistake_to_focus(mistake_key, target_minutes)

        # Reasons for "Why?" drawer
        reasons = self._build_reasons(
            workouts_7=workouts_7,
            workouts_14=workouts_14,
            target_days=target_days,
            max_gap=max_gap,
            volume_delta_pct=volume_delta_pct,
            mistake_key=mistake_key,
        )

        # Upsert UserBehaviorMetrics (unique on user_id, metrics_date)
        row = UserBehaviorMetrics(
            id=uuid4(),
            user_id=user_id,
            metrics_date=today,
            consistency_score=round(consistency_score, 1) if consistency_score is not None else None,
            dropout_risk=dropout_risk,
            burnout_risk=burnout_risk,
            momentum_trend=momentum_trend,
            adherence_type=adherence_type,
            workouts_last_7_days=workouts_7,
            workouts_last_14_days=workouts_14,
            avg_session_duration_minutes=round(avg_duration_7, 1) if avg_duration_7 is not None else None,
            total_volume_last_7_days=round(volume_7, 1) if volume_7 is not None else None,
            volume_delta_vs_prev_week=round(volume_delta_pct, 1) if volume_delta_pct is not None else None,
            max_gap_days=max_gap,
            common_skip_day=common_skip,
            primary_training_mistake_key=mistake_key,
            primary_training_mistake_label=mistake_label,
            weekly_focus_key=focus_key,
            weekly_focus_label=focus_label,
            reasons=reasons,
        )

        stmt = insert(UserBehaviorMetrics).values(
            id=row.id,
            user_id=row.user_id,
            metrics_date=row.metrics_date,
            consistency_score=row.consistency_score,
            dropout_risk=row.dropout_risk,
            burnout_risk=row.burnout_risk,
            momentum_trend=row.momentum_trend,
            adherence_type=row.adherence_type,
            workouts_last_7_days=row.workouts_last_7_days,
            workouts_last_14_days=row.workouts_last_14_days,
            avg_session_duration_minutes=row.avg_session_duration_minutes,
            total_volume_last_7_days=row.total_volume_last_7_days,
            volume_delta_vs_prev_week=row.volume_delta_vs_prev_week,
            max_gap_days=row.max_gap_days,
            common_skip_day=row.common_skip_day,
            primary_training_mistake_key=row.primary_training_mistake_key,
            primary_training_mistake_label=row.primary_training_mistake_label,
            weekly_focus_key=row.weekly_focus_key,
            weekly_focus_label=row.weekly_focus_label,
            reasons=row.reasons,
        ).on_conflict_do_update(
            index_elements=["user_id", "metrics_date"],
            set_={
                "consistency_score": row.consistency_score,
                "dropout_risk": row.dropout_risk,
                "burnout_risk": row.burnout_risk,
                "momentum_trend": row.momentum_trend,
                "adherence_type": row.adherence_type,
                "workouts_last_7_days": row.workouts_last_7_days,
                "workouts_last_14_days": row.workouts_last_14_days,
                "avg_session_duration_minutes": row.avg_session_duration_minutes,
                "total_volume_last_7_days": row.total_volume_last_7_days,
                "volume_delta_vs_prev_week": row.volume_delta_vs_prev_week,
                "max_gap_days": row.max_gap_days,
                "common_skip_day": row.common_skip_day,
                "primary_training_mistake_key": row.primary_training_mistake_key,
                "primary_training_mistake_label": row.primary_training_mistake_label,
                "weekly_focus_key": row.weekly_focus_key,
                "weekly_focus_label": row.weekly_focus_label,
                "reasons": row.reasons,
                "computed_at": func.now(),
            },
        )
        self.db.execute(stmt)
        self.db.flush()

        # Return the row we just upserted (reload to get computed_at etc.)
        return (
            self.db.query(UserBehaviorMetrics)
            .filter(
                UserBehaviorMetrics.user_id == user_id,
                UserBehaviorMetrics.metrics_date == today,
            )
            .first()
        )

    def _get_worked_out_dates(self, user_id: UUID, user_tz: str, days_back: int = 30) -> set[date]:
        """Set of dates (user TZ) when user had at least one finalized workout."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        q = text(f"""
            SELECT DISTINCT DATE(timezone('{user_tz}', start_time)) AS workout_date
            FROM workouts
            WHERE user_id = :user_id
              AND lifecycle_status = 'finalized'
              AND completion_status IN ('completed', 'partial')
              AND start_time >= :cutoff
        """)
        rows = self.db.execute(q, {"user_id": str(user_id), "cutoff": cutoff}).all()
        return {row.workout_date for row in rows}

    def _get_volume_and_duration(
        self, user_id: UUID, user_tz: str, today: date
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Returns (total_volume_last_7_days, total_volume_prev_7_days, avg_duration_last_7_days).
        Volume = sum(weight * reps) for working sets only.
        """
        start_7 = today - timedelta(days=6)
        end_7 = today
        start_14 = today - timedelta(days=13)
        end_prev_7 = today - timedelta(days=7)

        q_7 = text(f"""
            SELECT
                COALESCE(SUM((COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))), 0)::float AS vol,
                AVG(w.duration_minutes) AS avg_dur
            FROM workouts w
            JOIN workout_exercises we ON we.workout_id = w.id
            JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'finalized'
              AND w.completion_status IN ('completed', 'partial')
              AND ws.set_type = 'working'
              AND DATE(timezone('{user_tz}', w.start_time)) >= :start_date
              AND DATE(timezone('{user_tz}', w.start_time)) <= :end_date
        """)
        row_7 = self.db.execute(
            q_7,
            {"user_id": str(user_id), "start_date": start_7, "end_date": end_7},
        ).first()
        volume_7 = float(row_7.vol) if row_7 and row_7.vol is not None else 0.0
        avg_dur_7 = float(row_7.avg_dur) if row_7 and row_7.avg_dur is not None else None

        q_prev = text(f"""
            SELECT COALESCE(SUM((COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))), 0)::float AS vol
            FROM workouts w
            JOIN workout_exercises we ON we.workout_id = w.id
            JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'finalized'
              AND w.completion_status IN ('completed', 'partial')
              AND ws.set_type = 'working'
              AND DATE(timezone('{user_tz}', w.start_time)) >= :start_date
              AND DATE(timezone('{user_tz}', w.start_time)) <= :end_date
        """)
        row_prev = self.db.execute(
            q_prev,
            {"user_id": str(user_id), "start_date": start_14, "end_date": end_prev_7},
        ).first()
        volume_prev_7 = float(row_prev.vol) if row_prev and row_prev.vol is not None else 0.0

        return (volume_7, volume_prev_7, avg_dur_7)

    def _volume_delta_pct(
        self, volume_7: Optional[float], volume_prev_7: Optional[float]
    ) -> Optional[float]:
        """Percentage change: (current - prev) / prev * 100. None if prev is 0."""
        if volume_prev_7 is None or volume_prev_7 == 0:
            return None
        if volume_7 is None:
            return None
        return ((volume_7 - volume_prev_7) / volume_prev_7) * 100.0

    def _max_gap_days(self, worked_dates: set[date], today: date) -> Optional[int]:
        """Longest gap (consecutive days without workout) in the last 30 days."""
        if not worked_dates:
            return None
        window_start = today - timedelta(days=29)
        in_window = sorted([d for d in worked_dates if window_start <= d <= today])
        if not in_window:
            return (today - window_start).days
        gaps = []
        gaps.append((in_window[0] - window_start).days)
        for i in range(len(in_window) - 1):
            gaps.append((in_window[i + 1] - in_window[i]).days - 1)
        gaps.append((today - in_window[-1]).days)
        return max(gaps) if gaps else 0

    def _common_skip_day(
        self, worked_dates: set[date], today: date, days_back: int = 30
    ) -> Optional[str]:
        """Weekday (lowercase) most often without a workout in the window."""
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        skip_counts = [0] * 7
        start = today - timedelta(days=days_back - 1)
        d = start
        while d <= today:
            if d not in worked_dates:
                skip_counts[d.weekday()] += 1
            d += timedelta(days=1)
        max_idx = max(range(7), key=lambda i: skip_counts[i])
        return weekday_names[max_idx] if skip_counts[max_idx] > 0 else None

    def _consistency_score(self, workouts_14: int, target_days_per_week: int) -> float:
        """0–100: how well user hits target over 2 weeks. Cap at 100."""
        if target_days_per_week <= 0:
            return 100.0
        expected_2w = target_days_per_week * 2
        if expected_2w <= 0:
            return 100.0
        score = (workouts_14 / expected_2w) * 100.0
        return min(100.0, max(0.0, score))

    def _dropout_risk(self, workouts_14: int, max_gap_days: Optional[int]) -> str:
        """low | medium | high."""
        if workouts_14 == 0:
            return "high"
        if max_gap_days is not None and max_gap_days > 5:
            return "high"
        if max_gap_days is not None and max_gap_days > 3:
            return "medium"
        return "low"

    def _burnout_risk(
        self,
        workouts_14: int,
        avg_duration_7: Optional[float],
        target_minutes: int,
    ) -> str:
        """low | medium | high. MVP: simple heuristic."""
        if workouts_14 >= 10 and avg_duration_7 and avg_duration_7 >= 60:
            return "medium"
        if workouts_14 >= 12:
            return "high"
        return "low"

    def _momentum_trend(self, volume_delta_pct: Optional[float]) -> str:
        """rising | stable | falling."""
        if volume_delta_pct is None:
            return "stable"
        if volume_delta_pct > 10:
            return "rising"
        if volume_delta_pct < -15:
            return "falling"
        return "stable"

    def _adherence_type(
        self, worked_dates: set[date], today: date, max_gap_days: Optional[int]
    ) -> str:
        """consistent | weekend_warrior | sporadic."""
        if max_gap_days is not None and max_gap_days > 4:
            return "sporadic"
        recent = [d for d in worked_dates if (today - d).days <= 14]
        if not recent:
            return "sporadic"
        weekend_count = sum(1 for d in recent if d.weekday() >= 5)
        if weekend_count >= len(recent) * 0.6:
            return "weekend_warrior"
        return "consistent"

    def _detect_mistake(
        self,
        workouts_14: int,
        target_days: int,
        max_gap: Optional[int],
        volume_7: float,
        volume_prev_7: float,
        avg_duration_7: Optional[float],
        target_minutes: int,
        burnout_risk: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Apply 5 rules in priority order; return first match (key, label) or (None, None).
        """
        # 1. inconsistent_training_days
        threshold = max(0, target_days * 2 - 1)
        if workouts_14 < threshold or (max_gap is not None and max_gap > 4):
            return ("inconsistent_training_days", "Inconsistent Training Days")

        # 2. volume_drop: last 7 vs previous 7 down >= 25%
        if volume_prev_7 > 0 and volume_7 is not None:
            pct = ((volume_prev_7 - volume_7) / volume_prev_7) * 100.0
            if pct >= 25:
                return ("volume_drop", "Volume Drop")

        # 3. no_progression_21_days (optional MVP stub)
        # 4. overtraining_signals (optional MVP stub)

        # 5. sessions_too_short
        if target_minutes > 15 and avg_duration_7 is not None:
            if avg_duration_7 < (target_minutes - 15):
                return ("sessions_too_short", "Sessions Too Short")

        return (None, None)

    def _mistake_to_focus(
        self, mistake_key: Optional[str], target_minutes: int
    ) -> tuple[Optional[str], Optional[str]]:
        """Map mistake key to weekly_focus_key and weekly_focus_label."""
        if not mistake_key or mistake_key not in MISTAKE_TO_FOCUS:
            return (None, None)
        focus_key, focus_label = MISTAKE_TO_FOCUS[mistake_key]
        if "{target}" in focus_label:
            focus_label = focus_label.format(target=max(15, target_minutes - 15))
        return (focus_key, focus_label)

    def _build_reasons(
        self,
        workouts_7: int,
        workouts_14: int,
        target_days: int,
        max_gap: Optional[int],
        volume_delta_pct: Optional[float],
        mistake_key: Optional[str],
    ) -> list[dict]:
        """Build reasons list for Why drawer: [{"reason_key": "...", "reason_label": "..."}]."""
        reasons = []
        if target_days > 0 and workouts_14 < (target_days * 2):
            reasons.append({"reason_key": "missed_target", "reason_label": "Fewer than target workouts in last 2 weeks"})
        if max_gap is not None and max_gap > 4:
            reasons.append({"reason_key": "gap_4_days", "reason_label": f"Longest gap without training: {max_gap} days"})
        if volume_delta_pct is not None and volume_delta_pct < -20:
            reasons.append({"reason_key": "volume_drop", "reason_label": "Volume down vs previous week"})
        if mistake_key == "sessions_too_short":
            reasons.append({"reason_key": "sessions_too_short", "reason_label": "Average session length below target"})
        if mistake_key == "inconsistent_training_days":
            reasons.append({"reason_key": "inconsistent_training_days", "reason_label": "Training days are uneven"})
        return reasons
