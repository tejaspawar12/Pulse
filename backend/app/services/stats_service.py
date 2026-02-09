"""
Stats service: summary, streak, and volume over time.
Uses user timezone for all date boundaries (same as UserStatusService).
"""
import re
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.stats import (
    MetricsSummaryResponse,
    StatsSummaryResponse,
    StreakResponse,
    VolumeDataPoint,
    VolumeResponse,
)


def _sanitize_timezone(tz: str) -> str:
    """Allow only safe timezone chars (alphanumeric, underscore, slash, plus, minus)."""
    if not tz or not re.match(r"^[A-Za-z0-9_/+-]+$", tz):
        return "UTC"
    return tz


class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def _get_today_date(self, user_timezone: str) -> date:
        """Today's date in user timezone."""
        tz = _sanitize_timezone(user_timezone)
        try:
            q = text(f"SELECT DATE(timezone('{tz}', now())) AS today")
            result = self.db.execute(q)
            return result.scalar()
        except Exception:
            return datetime.now(timezone.utc).date()

    def _get_worked_out_dates(
        self, user_id: UUID, user_timezone: str, days_back: int = 365
    ) -> set[date]:
        """Set of dates (user TZ) when user had at least one finalized workout (completed/partial)."""
        tz = _sanitize_timezone(user_timezone)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        q = text(f"""
            SELECT DISTINCT DATE(timezone('{tz}', start_time)) AS workout_date
            FROM workouts
            WHERE user_id = :user_id
              AND lifecycle_status = 'finalized'
              AND completion_status IN ('completed', 'partial')
              AND start_time >= :cutoff
        """)
        rows = self.db.execute(q, {"user_id": str(user_id), "cutoff": cutoff}).all()
        return {row.workout_date for row in rows}

    def get_summary(
        self, user_id: UUID, user_timezone: str, days: int
    ) -> StatsSummaryResponse:
        """
        Summary stats for the period [today - (days-1), today] inclusive in user TZ.
        Only finalized workouts (completed/partial). Volume = sum of (weight * reps) for working sets.
        """
        tz = _sanitize_timezone(user_timezone)
        end_date = self._get_today_date(user_timezone)
        start_date = end_date - timedelta(days=days - 1)

        # Single query: workout count, total volume (working sets), total sets, avg duration
        # Volume formula (LOCKED): (weight or 0) * (reps or 0)
        q_sum = text(f"""
            SELECT
                COUNT(DISTINCT w.id) AS total_workouts,
                COALESCE(SUM(
                    (COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))
                ), 0)::float AS total_volume_kg,
                COUNT(ws.id) AS total_sets,
                AVG(w.duration_minutes) AS avg_duration
            FROM workouts w
            JOIN workout_exercises we ON we.workout_id = w.id
            JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'finalized'
              AND w.completion_status IN ('completed', 'partial')
              AND ws.set_type = 'working'
              AND DATE(timezone('{tz}', w.start_time)) >= :start_date
              AND DATE(timezone('{tz}', w.start_time)) <= :end_date
        """)
        row = self.db.execute(
            q_sum,
            {
                "user_id": str(user_id),
                "start_date": start_date,
                "end_date": end_date,
            },
        ).first()

        total_workouts = row.total_workouts or 0
        total_volume_kg = float(row.total_volume_kg or 0)
        total_sets = row.total_sets or 0
        avg_dur = row.avg_duration
        avg_workout_duration_minutes = float(avg_dur) if avg_dur is not None else None

        # Most trained muscle: primary_muscle_group with largest set count in period
        q_muscle = text(f"""
            SELECT el.primary_muscle_group
            FROM workouts w
            JOIN workout_exercises we ON we.workout_id = w.id
            JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            JOIN exercise_library el ON el.id = we.exercise_id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'finalized'
              AND w.completion_status IN ('completed', 'partial')
              AND ws.set_type = 'working'
              AND DATE(timezone('{tz}', w.start_time)) >= :start_date
              AND DATE(timezone('{tz}', w.start_time)) <= :end_date
            GROUP BY el.primary_muscle_group
            ORDER BY COUNT(ws.id) DESC
            LIMIT 1
        """)
        muscle_row = self.db.execute(
            q_muscle,
            {
                "user_id": str(user_id),
                "start_date": start_date,
                "end_date": end_date,
            },
        ).first()
        most_trained_muscle = muscle_row.primary_muscle_group if muscle_row else None

        return StatsSummaryResponse(
            period_days=days,
            total_workouts=total_workouts,
            total_volume_kg=total_volume_kg,
            total_sets=total_sets,
            prs_hit=0,
            avg_workout_duration_minutes=avg_workout_duration_minutes,
            most_trained_muscle=most_trained_muscle,
        )

    def get_streak(self, user_id: UUID, user_timezone: str) -> StreakResponse:
        """Current streak (from today backwards), longest streak, last workout date."""
        today = self._get_today_date(user_timezone)
        worked = self._get_worked_out_dates(user_id, user_timezone, days_back=365)

        if not worked:
            return StreakResponse(
                current_streak_days=0,
                longest_streak_days=0,
                last_workout_date=None,
            )

        last_workout_date = max(worked)

        # Current streak: from today backwards
        current = 0
        d = today
        while d in worked:
            current += 1
            d -= timedelta(days=1)

        # Longest streak: sort dates, find max consecutive run
        sorted_dates = sorted(worked)
        longest = 1
        run = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                run += 1
                longest = max(longest, run)
            else:
                run = 1

        return StreakResponse(
            current_streak_days=current,
            longest_streak_days=longest,
            last_workout_date=last_workout_date,
        )

    def get_volume_over_time(
        self, user_id: UUID, user_timezone: str, days: int, group_by: str
    ) -> VolumeResponse:
        """
        Volume over time: buckets by day or week (Monday–Sunday).
        Returns continuous buckets (missing days/weeks have workout_count=0, total_volume_kg=0).
        """
        tz = _sanitize_timezone(user_timezone)
        end_date = self._get_today_date(user_timezone)
        start_date = end_date - timedelta(days=days - 1)

        if group_by == "day":
            # One bucket per day; fill missing with zeros
            buckets: list[VolumeDataPoint] = []
            d = start_date
            while d <= end_date:
                buckets.append(
                    VolumeDataPoint(
                        period_start=d,
                        period_end=d,
                        total_volume_kg=0.0,
                        workout_count=0,
                    )
                )
                d += timedelta(days=1)

            # Query: per-day aggregates
            q = text(f"""
                SELECT
                    DATE(timezone('{tz}', w.start_time)) AS bucket_date,
                    COUNT(DISTINCT w.id) AS workout_count,
                    COALESCE(SUM(
                        (COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))
                    ), 0)::float AS total_volume_kg
                FROM workouts w
                JOIN workout_exercises we ON we.workout_id = w.id
                JOIN workout_sets ws ON ws.workout_exercise_id = we.id
                WHERE w.user_id = :user_id
                  AND w.lifecycle_status = 'finalized'
                  AND w.completion_status IN ('completed', 'partial')
                  AND ws.set_type = 'working'
                  AND DATE(timezone('{tz}', w.start_time)) >= :start_date
                  AND DATE(timezone('{tz}', w.start_time)) <= :end_date
                GROUP BY DATE(timezone('{tz}', w.start_time))
            """)
            rows = self.db.execute(
                q,
                {"user_id": str(user_id), "start_date": start_date, "end_date": end_date},
            ).all()

            by_date = {(row.bucket_date): (row.workout_count, float(row.total_volume_kg or 0)) for row in rows}
            for i, b in enumerate(buckets):
                wc, vol = by_date.get(b.period_start, (0, 0.0))
                buckets[i] = VolumeDataPoint(
                    period_start=b.period_start,
                    period_end=b.period_end,
                    total_volume_kg=vol,
                    workout_count=wc,
                )
            return VolumeResponse(data=buckets, period_days=days)
        else:
            # group_by == "week": buckets are Monday–Sunday (ISO week)
            # Build list of week buckets that overlap [start_date, end_date]
            # Monday of week containing start_date
            start_week_monday = start_date - timedelta(days=start_date.weekday())
            buckets = []
            monday = start_week_monday
            while monday <= end_date:
                sunday = monday + timedelta(days=6)
                buckets.append(
                    VolumeDataPoint(
                        period_start=monday,
                        period_end=sunday,
                        total_volume_kg=0.0,
                        workout_count=0,
                    )
                )
                monday += timedelta(days=7)

            # Query: aggregate by week (Monday = start of week; date_trunc('week', ...) is ISO/Monday in PostgreSQL)
            q = text(f"""
                SELECT
                    (date_trunc('week', timezone('{tz}', w.start_time))::date) AS period_start,
                    COUNT(DISTINCT w.id) AS workout_count,
                    COALESCE(SUM(
                        (COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))
                    ), 0)::float AS total_volume_kg
                FROM workouts w
                JOIN workout_exercises we ON we.workout_id = w.id
                JOIN workout_sets ws ON ws.workout_exercise_id = we.id
                WHERE w.user_id = :user_id
                  AND w.lifecycle_status = 'finalized'
                  AND w.completion_status IN ('completed', 'partial')
                  AND ws.set_type = 'working'
                  AND DATE(timezone('{tz}', w.start_time)) >= :start_date
                  AND DATE(timezone('{tz}', w.start_time)) <= :end_date
                GROUP BY date_trunc('week', timezone('{tz}', w.start_time))
                ORDER BY period_start
            """)
            rows = self.db.execute(
                q,
                {"user_id": str(user_id), "start_date": start_date, "end_date": end_date},
            ).all()

            by_week = {}
            for row in rows:
                ps = row.period_start
                if hasattr(ps, "date"):
                    ps = ps.date() if callable(getattr(ps, "date", None)) else ps
                by_week[ps] = (row.workout_count, float(row.total_volume_kg or 0))

            for i, b in enumerate(buckets):
                wc, vol = by_week.get(b.period_start, (0, 0.0))
                buckets[i] = VolumeDataPoint(
                    period_start=b.period_start,
                    period_end=b.period_end,
                    total_volume_kg=vol,
                    workout_count=wc,
                )
            return VolumeResponse(data=buckets, period_days=days)

    def get_volume_by_muscle_group(
        self, user_id: UUID, user_timezone: str, days: int
    ) -> dict[str, float]:
        """
        Total volume (weight * reps) per primary_muscle_group for the period.
        Only finalized workouts, working sets. Keys are lowercase (e.g. chest, back, legs).
        """
        tz = _sanitize_timezone(user_timezone)
        end_date = self._get_today_date(user_timezone)
        start_date = end_date - timedelta(days=days - 1)
        q = text(f"""
            SELECT
                LOWER(el.primary_muscle_group) AS muscle_group,
                COALESCE(SUM(
                    (COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0))
                ), 0)::float AS volume_kg
            FROM workouts w
            JOIN workout_exercises we ON we.workout_id = w.id
            JOIN workout_sets ws ON ws.workout_exercise_id = we.id
            JOIN exercise_library el ON el.id = we.exercise_id
            WHERE w.user_id = :user_id
              AND w.lifecycle_status = 'finalized'
              AND w.completion_status IN ('completed', 'partial')
              AND ws.set_type = 'working'
              AND DATE(timezone('{tz}', w.start_time)) >= :start_date
              AND DATE(timezone('{tz}', w.start_time)) <= :end_date
            GROUP BY LOWER(el.primary_muscle_group)
        """)
        rows = self.db.execute(
            q,
            {
                "user_id": str(user_id),
                "start_date": start_date,
                "end_date": end_date,
            },
        ).all()
        return {row.muscle_group: float(row.volume_kg or 0) for row in rows}

    def get_imbalance_hint(self, volume_by_muscle: dict[str, float]) -> str | None:
        """
        Simple rule: if chest/legs or push/pull ratio > 2.0, suggest balancing.
        Returns a short hint or None.
        """
        chest = volume_by_muscle.get("chest", 0.0)
        back = volume_by_muscle.get("back", 0.0)
        legs = volume_by_muscle.get("legs", 0.0)
        if legs <= 0:
            if chest > 0 or back > 0:
                return "Consider adding leg volume for balance."
            return None
        upper = chest + back
        if upper / legs > 2.0:
            return "Consider more leg volume for balance."
        return None

    def get_metrics_summary(
        self, user_id: UUID, user_timezone: str, days: int
    ) -> MetricsSummaryResponse:
        """
        Phase 3: Single metrics payload for Insights (days=7 or 30).
        Aggregates summary, streak, volume_by_muscle_group, imbalance_hint.
        """
        summary = self.get_summary(user_id, user_timezone, days)
        streak = self.get_streak(user_id, user_timezone)
        volume_by_muscle = self.get_volume_by_muscle_group(user_id, user_timezone, days)
        imbalance_hint = self.get_imbalance_hint(volume_by_muscle)
        weeks = max(1, days / 7.0)
        workouts_per_week = summary.total_workouts / weeks
        return MetricsSummaryResponse(
            total_volume_kg=summary.total_volume_kg,
            workouts_count=summary.total_workouts,
            workouts_per_week=round(workouts_per_week, 1),
            volume_by_muscle_group=volume_by_muscle,
            pr_count=summary.prs_hit,
            imbalance_hint=imbalance_hint,
            streak_days=streak.current_streak_days,
            period_days=days,
        )
