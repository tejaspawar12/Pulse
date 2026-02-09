# Backend Jobs (Phase 2 Week 5 Day 6)

## Nightly job: behavior metrics

**File**: `app/jobs/nightly_job.py`

**Purpose**: Compute `UserBehaviorMetrics` for active users so the coach has fresh metrics when users open the app.

**Active users**: Users who have at least one finalized workout (completed or partial) in the last 30 days.

**Metrics date**: For each user, `metrics_date = user_today(user.timezone)` at job runtime (so late-night users get the correct "today" in their timezone).

**Error isolation**: Per-user try/except; one user's failure is logged and does not stop the job. Failed users get a rollback; successful users are committed.

### How to run

From the **backend** directory, with your virtualenv activated and `.env` set (same as running uvicorn):

```bash
# Process all active users
python -m app.jobs.nightly_job

# Process at most 100 users (e.g. for testing or rate-limiting)
python -m app.jobs.nightly_job --limit 100
```

**Scheduling (MVP)**:

- Run manually once per day, or
- Cron example (run at 2 AM UTC daily):
  ```cron
  0 2 * * * cd /path/to/backend && . venv/bin/activate && python -m app.jobs.nightly_job --limit 500
  ```
- Windows Task Scheduler: create a daily task that runs `python -m app.jobs.nightly_job` with the backend directory as working directory and the same env as the API.

**Exit code**: `0` if all users processed successfully; `1` if any user failed (so cron can alert on failure).

### Optional: LLM usage log

After processing users, the job logs how many users had non-zero coach usage today (UTC) from `llm_usage_daily` — for visibility and future rate-limiting.

---

## Weekly job: report + prediction (Phase 2 Week 6)

**File**: `app/jobs/weekly_job.py`

**Purpose**: For each Pro/trial user, if it is **Monday 03:00–05:59 AM** in the user's timezone, generate the weekly training report and transformation prediction. Idempotent on `(user_id, week_start)` so no duplicate reports.

**Report window**: Monday **03:00–05:59 AM** user-local (3 hours). More forgiving if the server misses one hour (deploy, outage).

**Error isolation**: Per-user try/except; one user's failure is logged and does not stop the job.

### How to run

From the **backend** directory, with your virtualenv activated and `.env` set:

```bash
python -m app.jobs.weekly_job
```

**Scheduling (MVP)**:

- Run **every hour** so that users in any timezone hit the 3-hour Monday window:
  ```cron
  0 * * * * cd /path/to/backend && . venv/bin/activate && python -m app.jobs.weekly_job
  ```
- Windows Task Scheduler: create an hourly task that runs `python -m app.jobs.weekly_job` with the backend directory as working directory.

**Exit code**: `0` if all users in the window processed successfully; `1` if any user failed.
