"""
Weekly job: transformation prediction + plan adjustment + weekly report for all users (Phase 2 Week 6 + 7).

Purpose:
  - Run every hour (cron 0 * * * *).
  - For each user in Monday 03:00–05:59 AM (user's timezone): generate transformation prediction, plan adjustment (if auto_adjust), and weekly report.
  - Per-user error isolation: one user's failure is logged and does not stop the job.

How to run (MVP: manual or cron hourly):
  From backend directory:
    python -m app.jobs.weekly_job

  Cron example (run every hour):
    0 * * * * cd /path/to/backend && python -m app.jobs.weekly_job

  Report window: Monday 03:00–05:59 AM user-local (3 hours).
"""
import logging
import sys
from datetime import datetime, timedelta, timezone

import pytz
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.user import User
from app.services.report_service import ReportService
from app.services.prediction_service import PredictionService
from app.services.plan_service import PlanService
from app.utils.timezone import user_today

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _sanitize_timezone(tz: str) -> str:
    import re
    if not tz or not re.match(r"^[A-Za-z0-9_/+-]+$", tz):
        return "UTC"
    return tz


def _is_report_window(user: User, now_utc: datetime) -> bool:
    """
    True if user's local time is Monday 03:00–05:59 AM (3-hour window).
    weekday(): Mon=0, ..., Sun=6.
    """
    tz_name = _sanitize_timezone(user.timezone or "Asia/Kolkata")
    try:
        tz = pytz.timezone(tz_name)
        local = now_utc.astimezone(tz)
        if local.weekday() != 0:
            return False
        return 3 <= local.hour < 6
    except Exception:
        return False


def run_weekly_job() -> tuple[int, int]:
    """
    For each user in report window (Monday 03:00–05:59 user TZ): generate transformation prediction, plan adjustment (if auto_adjust), and weekly report.
    Returns (success_count, error_count).
    """
    now_utc = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        in_window = [u for u in users if _is_report_window(u, now_utc)]
        if not in_window:
            logger.debug("No users in report window (Monday 03:00–05:59 local).")
            return 0, 0

        logger.info("Found %d user(s) in report window. Generating prediction, plan adjustment, and report for all.", len(in_window))
        report_svc = ReportService(db)
        prediction_svc = PredictionService(db)
        plan_svc = PlanService(db)
        success_count = 0
        error_count = 0

        for u in in_window:
            try:
                # Transformation prediction: for everyone
                prediction_svc.compute_prediction(u.id)
                tz = _sanitize_timezone(u.timezone or "Asia/Kolkata")
                today = user_today(tz)
                this_week_start = today - timedelta(days=today.weekday())
                # Plan adjustment: for everyone with auto_adjust enabled (service no-ops otherwise)
                plan_svc.compute_weekly_adjustment(u.id, this_week_start)
                # Weekly report: for everyone
                report_svc.generate_weekly_report(u.id)
                success_count += 1
            except Exception as e:
                logger.exception("Weekly job failed for user_id=%s: %s", u.id, e)
                db.rollback()
                error_count += 1

        logger.info("Weekly job done. success=%d, errors=%d", success_count, error_count)
        return success_count, error_count
    finally:
        db.close()


def main() -> int:
    parser = __import__("argparse").ArgumentParser(
        description="Weekly job: prediction + plan adjustment + report for all users, in Monday 03:00–05:59 window.",
    )
    parser.parse_args()
    success, errors = run_weekly_job()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
