"""
Nightly job: compute behavior metrics for active users (Phase 2 Week 5 Day 6).

Purpose:
  - Compute UserBehaviorMetrics for users who have at least one finalized workout
    in the last 30 days, so the coach has fresh metrics when users open the app.
  - Metrics date is each user's "today" in their timezone (user_today(user.timezone)).
  - Per-user error isolation: one user's failure is logged and does not stop the job.

How to run (MVP: manual or cron once per day):
  From backend directory:
    python -m app.jobs.nightly_job [--limit N]

  Examples:
    python -m app.jobs.nightly_job              # process all active users
    python -m app.jobs.nightly_job --limit 100   # process up to 100 users

  Cron example (run at 2 AM UTC daily):
    0 2 * * * cd /path/to/backend && python -m app.jobs.nightly_job --limit 500
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.settings import settings
from app.models.user import User
from app.models.workout import Workout
from app.models.llm_usage_daily import LLMUsageDaily
from app.utils.enums import LifecycleStatus, CompletionStatus
from app.utils.timezone import user_today
from app.services.intelligence_service import IntelligenceService
from app.services.coach_service import delete_old_coach_chat_messages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Default cap for safety (None = no limit)
DEFAULT_LIMIT = None


def get_active_user_ids(db: Session, days_back: int = 30, limit: int | None = None) -> list[UUID]:
    """
    Return user_ids that have at least one finalized workout in the last `days_back` days.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    q = (
        db.query(distinct(Workout.user_id))
        .filter(
            Workout.lifecycle_status == LifecycleStatus.FINALIZED.value,
            Workout.completion_status.in_([CompletionStatus.COMPLETED.value, CompletionStatus.PARTIAL.value]),
            Workout.start_time >= cutoff,
        )
    )
    if limit is not None:
        q = q.limit(limit)
    rows = q.all()
    return [row[0] for row in rows]


def run_nightly_job(limit: int | None = DEFAULT_LIMIT) -> tuple[int, int]:
    """
    Compute behavior metrics for all active users. Returns (success_count, error_count).
    """
    db = SessionLocal()
    try:
        user_ids = get_active_user_ids(db, days_back=30, limit=limit)
        if not user_ids:
            logger.info("No active users (no finalized workout in last 30 days).")
            return 0, 0

        logger.info("Found %d active user(s). Computing metrics (metrics_date = user's today).", len(user_ids))

        # Load users to get timezone (we need User for user_today)
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_by_id = {u.id: u for u in users}

        success_count = 0
        error_count = 0
        intel = IntelligenceService(db)

        for user_id in user_ids:
            user = user_by_id.get(user_id)
            if not user:
                logger.warning("User %s not found, skip.", user_id)
                error_count += 1
                continue

            tz = (user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
            metrics_date = user_today(tz)

            try:
                intel.compute_metrics(user_id, metrics_date=metrics_date)
                db.commit()
                success_count += 1
            except Exception as e:
                logger.exception("Metrics failed for user_id=%s (metrics_date=%s): %s", user_id, metrics_date, e)
                db.rollback()
                error_count += 1

        logger.info("Nightly job done. success=%d, errors=%d", success_count, error_count)

        # Coach chat retention: delete messages older than COACH_CHAT_RETENTION_DAYS (1 = new day, new messages)
        retention_days = getattr(settings, "COACH_CHAT_RETENTION_DAYS", 0)
        if retention_days > 0:
            try:
                deleted = delete_old_coach_chat_messages(db, retention_days)
                if deleted > 0:
                    db.commit()
            except Exception as e:
                logger.exception("Coach chat cleanup failed: %s", e)
                db.rollback()

        # Optional: log LLM usage for users approaching limit (for future rate-limiting)
        _log_usage_warnings(db)

        return success_count, error_count
    finally:
        db.close()


def _log_usage_warnings(db: Session) -> None:
    """Log users with non-zero coach usage today (UTC date) for visibility / future rate-limiting."""
    today_utc = datetime.now(timezone.utc).date()
    rows = (
        db.query(LLMUsageDaily)
        .filter(
            LLMUsageDaily.usage_date == today_utc,
            LLMUsageDaily.coach_calls > 0,
        )
        .all()
    )
    if rows:
        total_calls = sum(r.coach_calls for r in rows)
        logger.info("LLM usage today (UTC): %d user(s) with coach_calls, total coach_calls=%d", len(rows), total_calls)
    else:
        logger.debug("No coach usage recorded for today (UTC).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Nightly job: compute behavior metrics for active users (Phase 2 Week 5 Day 6)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process at most N active users (default: no limit)",
    )
    args = parser.parse_args()
    success, errors = run_nightly_job(limit=args.limit)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
