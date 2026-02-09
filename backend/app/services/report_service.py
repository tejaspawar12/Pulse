"""
Report service: weekly training report generation (Phase 2 Week 6).
Generates per-user, per-week report with diagnosis and optional LLM narrative.
"""
import re
from datetime import date, datetime, timedelta, time
from typing import Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.models.user import User
from app.models.user_coach_profile import UserCoachProfile
from app.models.workout import Workout
from app.models.weekly_training_report import WeeklyTrainingReport
from app.utils.timezone import user_today
from app.utils.enums import LifecycleStatus, CompletionStatus

# Reuse IntelligenceService mistake->focus mapping
from app.services.intelligence_service import MISTAKE_TO_FOCUS

DEFAULT_TARGET_DAYS_PER_WEEK = 3
DEFAULT_TARGET_SESSION_MINUTES = 45


def _sanitize_timezone(tz: str) -> str:
    if not tz or not re.match(r"^[A-Za-z0-9_/+-]+$", tz):
        return "UTC"
    return tz


def _local_date_to_utc_range(user_tz: str, day_start: date, day_end_inclusive: date):
    """
    Convert user-local date range to UTC datetimes (exclusive end).
    start_utc = day_start 00:00:00 in user TZ -> UTC
    end_utc = (day_end_inclusive + 1) 00:00:00 in user TZ -> UTC
    """
    tz = pytz.timezone(_sanitize_timezone(user_tz))
    start_local = datetime.combine(day_start, time(0, 0, 0))
    end_local = datetime.combine(day_end_inclusive + timedelta(days=1), time(0, 0, 0))
    start_local = tz.localize(start_local)
    end_local = tz.localize(end_local)
    start_utc = start_local.astimezone(pytz.UTC)
    end_utc = end_local.astimezone(pytz.UTC)
    return start_utc, end_utc


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_weekly_report(self, user_id: UUID) -> WeeklyTrainingReport:
        """
        Generate weekly report for the last completed week (Monday–Sunday in user TZ).
        Idempotent on (user_id, week_start). If < 2 workouts -> status='insufficient_data', no narrative.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        user_tz = _sanitize_timezone(user.timezone or "Asia/Kolkata")
        week_start, week_end = self._get_last_week_bounds(user_id)
        existing = (
            self.db.query(WeeklyTrainingReport)
            .filter(
                WeeklyTrainingReport.user_id == user_id,
                WeeklyTrainingReport.week_start == week_start,
            )
            .first()
        )
        if existing:
            return existing

        workouts = self._get_week_workouts(user_id, week_start, week_end, user_tz)
        if len(workouts) < 2:
            report = WeeklyTrainingReport(
                id=uuid4(),
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                workouts_count=len(workouts),
                total_volume_kg=None,
                volume_delta_pct=None,
                prs_hit=0,
                avg_session_duration=None,
                primary_training_mistake_key=None,
                primary_training_mistake_label=None,
                weekly_focus_key=None,
                weekly_focus_label=None,
                positive_signal_key=None,
                positive_signal_label=None,
                positive_signal_reason=None,
                reasons=None,
                narrative=None,
                narrative_source=None,
                status="insufficient_data",
            )
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            return report

        aggregates = self._compute_aggregates(user_id, week_start, week_end, user_tz, workouts)
        diagnosis = self._compute_week_diagnosis(
            user_id, week_start, week_end, workouts, user_tz
        )
        learning = self._detect_learning_feedback(
            aggregates.get("total_volume_kg") or 0,
            aggregates.get("volume_delta_pct"),
            aggregates.get("workouts_count", 0),
            aggregates.get("avg_session_duration"),
            user_id,
            week_start,
            user_tz,
        )

        narrative_text = None
        narrative_source_val = None
        from app.services.llm_service import llm_service
        diagnosis_json = {
            "workouts_count": aggregates.get("workouts_count"),
            "volume_delta_pct": aggregates.get("volume_delta_pct"),
            "primary_training_mistake_key": diagnosis.get("primary_training_mistake_key"),
            "weekly_focus_key": diagnosis.get("weekly_focus_key"),
            "positive_signal_key": learning.get("key"),
        }
        if user.weight_kg is not None:
            diagnosis_json["user_weight_kg"] = round(user.weight_kg, 1)
        if user.height_cm is not None:
            diagnosis_json["user_height_cm"] = round(user.height_cm, 1)
        if user.date_of_birth is not None:
            age = week_end.year - user.date_of_birth.year - (
                (week_end.month, week_end.day) < (user.date_of_birth.month, user.date_of_birth.day)
            )
            diagnosis_json["user_age_years"] = max(0, age)
        if user.gender:
            diagnosis_json["user_gender"] = user.gender
        narrative_text = llm_service.generate_weekly_narrative(
            user_id, diagnosis_json, self.db
        )
        if narrative_text is not None:
            narrative_source_val = "llm"
        else:
            narrative_text = self._fallback_narrative(
                aggregates, diagnosis, learning
            )
            narrative_source_val = "fallback"

        report = WeeklyTrainingReport(
            id=uuid4(),
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            workouts_count=aggregates.get("workouts_count"),
            total_volume_kg=aggregates.get("total_volume_kg"),
            volume_delta_pct=aggregates.get("volume_delta_pct"),
            prs_hit=aggregates.get("prs_hit", 0),
            avg_session_duration=aggregates.get("avg_session_duration"),
            primary_training_mistake_key=diagnosis.get("primary_training_mistake_key"),
            primary_training_mistake_label=diagnosis.get("primary_training_mistake_label"),
            weekly_focus_key=diagnosis.get("weekly_focus_key"),
            weekly_focus_label=diagnosis.get("weekly_focus_label"),
            positive_signal_key=learning.get("key"),
            positive_signal_label=learning.get("label"),
            positive_signal_reason=learning.get("reason"),
            reasons=diagnosis.get("reasons"),
            narrative=narrative_text,
            narrative_source=narrative_source_val,
            status="generated",
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def _get_last_week_bounds(self, user_id: UUID) -> tuple[date, date]:
        """Last completed week (Monday–Sunday) in user timezone."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        user_tz = _sanitize_timezone(user.timezone or "Asia/Kolkata")
        today = user_today(user_tz)
        end_of_last_week = today - timedelta(days=today.weekday() + 1)
        week_start = end_of_last_week - timedelta(days=6)
        return (week_start, end_of_last_week)

    def _get_week_workouts(
        self, user_id: UUID, week_start: date, week_end: date, user_tz: str
    ):
        """Workouts finalized in that week (user TZ). Timezone-safe: week bounds -> UTC."""
        start_utc, end_utc = _local_date_to_utc_range(user_tz, week_start, week_end)
        return (
            self.db.query(Workout)
            .filter(
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.FINALIZED.value,
                Workout.completion_status.in_([
                    CompletionStatus.COMPLETED.value,
                    CompletionStatus.PARTIAL.value,
                ]),
                Workout.end_time >= start_utc,
                Workout.end_time < end_utc,
            )
            .all()
        )

    def _compute_aggregates(
        self,
        user_id: UUID,
        week_start: date,
        week_end: date,
        user_tz: str,
        workouts: list,
    ) -> dict:
        """total_volume_kg, volume_delta_pct (vs previous week), avg_session_duration, prs_hit."""
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_end - timedelta(days=7)
        prev_workouts = self._get_week_workouts(
            user_id, prev_week_start, prev_week_end, user_tz
        )
        tz = _sanitize_timezone(user_tz)
        # Volume this week: sum(weight * reps) working sets for these workouts
        workout_ids = [w.id for w in workouts]
        if not workout_ids:
            total_volume_kg = 0.0
            avg_dur = None
        else:
            q = text("""
                SELECT
                    COALESCE(SUM((COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))), 0)::float AS vol,
                    AVG(w.duration_minutes) AS avg_dur
                FROM workouts w
                JOIN workout_exercises we ON we.workout_id = w.id
                JOIN workout_sets ws ON ws.workout_exercise_id = we.id
                WHERE w.id = ANY(:ids) AND ws.set_type = 'working'
            """)
            row = self.db.execute(q, {"ids": [str(i) for i in workout_ids]}).first()
            total_volume_kg = float(row.vol) if row and row.vol is not None else 0.0
            avg_dur = float(row.avg_dur) if row and row.avg_dur is not None else None
        prev_workout_ids = [w.id for w in prev_workouts]
        if prev_workout_ids:
            q_prev = text("""
                SELECT COALESCE(SUM((COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))), 0)::float AS vol
                FROM workouts w
                JOIN workout_exercises we ON we.workout_id = w.id
                JOIN workout_sets ws ON ws.workout_exercise_id = we.id
                WHERE w.id = ANY(:ids) AND ws.set_type = 'working'
            """)
            row_prev = self.db.execute(
                q_prev, {"ids": [str(i) for i in prev_workout_ids]}
            ).first()
            prev_volume = float(row_prev.vol) if row_prev and row_prev.vol else 0.0
        else:
            prev_volume = 0.0
        volume_delta_pct = None
        if prev_volume > 0:
            volume_delta_pct = ((total_volume_kg - prev_volume) / prev_volume) * 100.0
        return {
            "workouts_count": len(workouts),
            "total_volume_kg": round(total_volume_kg, 1) if total_volume_kg is not None else None,
            "volume_delta_pct": round(volume_delta_pct, 1) if volume_delta_pct is not None else None,
            "avg_session_duration": round(avg_dur, 1) if avg_dur is not None else None,
            "prs_hit": 0,
        }

    def _compute_week_diagnosis(
        self,
        user_id: UUID,
        week_start: date,
        week_end: date,
        workouts: list,
        user_tz: str,
    ) -> dict:
        """Week-limited diagnosis: mistake, focus, reasons from this week's data."""
        profile = self.db.query(UserCoachProfile).filter(
            UserCoachProfile.user_id == user_id
        ).first()
        target_days = (
            (profile.target_days_per_week if profile else None) or DEFAULT_TARGET_DAYS_PER_WEEK
        )
        target_minutes = (
            (profile.target_session_minutes if profile else None)
            or DEFAULT_TARGET_SESSION_MINUTES
        )
        workouts_count = len(workouts)
        aggregates = self._compute_aggregates(
            user_id, week_start, week_end, user_tz, workouts
        )
        volume_week = aggregates.get("total_volume_kg") or 0.0
        avg_duration = aggregates.get("avg_session_duration")
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_end - timedelta(days=7)
        prev_workouts = self._get_week_workouts(
            user_id, prev_week_start, prev_week_end, user_tz
        )
        prev_agg = self._compute_aggregates(
            user_id, prev_week_start, prev_week_end, user_tz, prev_workouts
        )
        volume_prev_week = prev_agg.get("total_volume_kg") or 0.0
        volume_delta_pct = None
        if volume_prev_week > 0:
            volume_delta_pct = ((volume_week - volume_prev_week) / volume_prev_week) * 100.0
        worked_dates_week = set()
        for w in workouts:
            if w.end_time:
                local_dt = w.end_time.astimezone(pytz.timezone(user_tz))
                worked_dates_week.add(local_dt.date())
        max_gap = self._max_gap_in_week(worked_dates_week, week_start, week_end)
        burnout_risk = "low"
        if workouts_count >= 6 and avg_duration and avg_duration >= 60:
            burnout_risk = "medium"
        if workouts_count >= 7:
            burnout_risk = "high"
        mistake_key, mistake_label = self._detect_mistake_week(
            workouts_count=workouts_count,
            target_days=target_days,
            max_gap=max_gap,
            volume_week=volume_week,
            volume_prev_week=volume_prev_week,
            avg_duration_week=avg_duration,
            target_minutes=target_minutes,
            burnout_risk=burnout_risk,
        )
        focus_key, focus_label = self._mistake_to_focus(mistake_key, target_minutes)
        reasons = self._build_reasons_week(
            workouts_count=workouts_count,
            target_days=target_days,
            max_gap=max_gap,
            volume_delta_pct=volume_delta_pct,
            mistake_key=mistake_key,
        )
        return {
            "primary_training_mistake_key": mistake_key,
            "primary_training_mistake_label": mistake_label,
            "weekly_focus_key": focus_key,
            "weekly_focus_label": focus_label,
            "reasons": reasons,
        }

    def _max_gap_in_week(
        self, worked_dates: set[date], week_start: date, week_end: date
    ) -> Optional[int]:
        """Longest gap (days) without a workout within the week."""
        if not worked_dates:
            return 7
        in_week = sorted([d for d in worked_dates if week_start <= d <= week_end])
        if not in_week:
            return 7
        gaps = []
        gaps.append((in_week[0] - week_start).days)
        for i in range(len(in_week) - 1):
            gaps.append((in_week[i + 1] - in_week[i]).days - 1)
        gaps.append((week_end - in_week[-1]).days)
        return max(gaps) if gaps else 0

    def _detect_mistake_week(
        self,
        workouts_count: int,
        target_days: int,
        max_gap: Optional[int],
        volume_week: float,
        volume_prev_week: float,
        avg_duration_week: Optional[float],
        target_minutes: int,
        burnout_risk: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Same priority order as IntelligenceService, week-scoped."""
        if workouts_count < target_days or (max_gap is not None and max_gap > 4):
            return ("inconsistent_training_days", "Inconsistent Training Days")
        if volume_prev_week > 0:
            pct = ((volume_prev_week - volume_week) / volume_prev_week) * 100.0
            if pct >= 25:
                return ("volume_drop", "Volume Drop")
        if target_minutes > 15 and avg_duration_week is not None:
            if avg_duration_week < (target_minutes - 15):
                return ("sessions_too_short", "Sessions Too Short")
        return (None, None)

    def _mistake_to_focus(
        self, mistake_key: Optional[str], target_minutes: int
    ) -> tuple[Optional[str], Optional[str]]:
        if not mistake_key or mistake_key not in MISTAKE_TO_FOCUS:
            return (None, None)
        focus_key, focus_label = MISTAKE_TO_FOCUS[mistake_key]
        if "{target}" in focus_label:
            focus_label = focus_label.format(target=max(15, target_minutes - 15))
        return (focus_key, focus_label)

    def _build_reasons_week(
        self,
        workouts_count: int,
        target_days: int,
        max_gap: Optional[int],
        volume_delta_pct: Optional[float],
        mistake_key: Optional[str],
    ) -> list[dict]:
        reasons = []
        if target_days > 0 and workouts_count < target_days:
            reasons.append({
                "reason_key": "missed_target",
                "reason_label": "Fewer than target workouts this week",
            })
        if max_gap is not None and max_gap > 4:
            reasons.append({
                "reason_key": "gap_4_days",
                "reason_label": f"Longest gap without training: {max_gap} days",
            })
        if volume_delta_pct is not None and volume_delta_pct < -20:
            reasons.append({
                "reason_key": "volume_drop",
                "reason_label": "Volume down vs previous week",
            })
        if mistake_key == "sessions_too_short":
            reasons.append({
                "reason_key": "sessions_too_short",
                "reason_label": "Average session length below target",
            })
        if mistake_key == "inconsistent_training_days":
            reasons.append({
                "reason_key": "inconsistent_training_days",
                "reason_label": "Training days are uneven",
            })
        return reasons

    def _detect_learning_feedback(
        self,
        total_volume_kg: float,
        volume_delta_pct: Optional[float],
        workouts_count: int,
        avg_session_duration: Optional[float],
        user_id: UUID,
        week_start: date,
        user_tz: str,
    ) -> dict:
        """Compare this week vs previous week aggregates; return one positive signal."""
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_end - timedelta(days=7)
        prev_workouts = self._get_week_workouts(
            user_id, prev_week_start, prev_week_end, user_tz
        )
        prev_agg = self._compute_aggregates(
            user_id, prev_week_start, prev_week_end, user_tz, prev_workouts
        )
        prev_volume = prev_agg.get("total_volume_kg") or 0.0
        prev_count = prev_agg.get("workouts_count") or 0
        prev_avg_dur = prev_agg.get("avg_session_duration")
        if prev_volume > 0 and volume_delta_pct is not None and volume_delta_pct > 5:
            pct = round(volume_delta_pct, 0)
            return {
                "key": "volume_up",
                "label": "Volume Up",
                "reason": f"Volume up {pct}% vs last week",
            }
        if workouts_count > prev_count and prev_count >= 0:
            return {
                "key": "consistency_up",
                "label": "Consistency Up",
                "reason": "More workouts than last week",
            }
        if (
            avg_session_duration is not None
            and prev_avg_dur is not None
            and avg_session_duration > prev_avg_dur + 5
        ):
            return {
                "key": "duration_up",
                "label": "Longer Sessions",
                "reason": "Average session length increased",
            }
        return {"key": None, "label": None, "reason": None}

    def _fallback_narrative(
        self, aggregates: dict, diagnosis: dict, learning: dict
    ) -> str:
        """Deterministic honest summary when LLM is not used or failed."""
        count = aggregates.get("workouts_count", 0)
        focus_label = diagnosis.get("weekly_focus_label") or "Keep training consistently"
        signal_label = learning.get("label") or ""
        parts = [f"This week you completed {count} workouts. Focus next week on {focus_label}."]
        if signal_label:
            parts.append(signal_label)
        return " ".join(parts)
