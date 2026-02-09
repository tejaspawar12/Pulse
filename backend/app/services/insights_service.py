"""
Phase 3 — Insights service: metrics + optional LLM narrative; cache; rate limit; fallback.
GET /ai/insights uses this. Cache key (user_id, days, window_end_date). Rate limit 5/day.
"""
import json
import logging
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.schemas.ai import AIInsightsResponse, NextWorkoutItem
from app.schemas.stats import MetricsSummaryResponse
from app.services.llm_service import LLMService
from app.services.stats_service import StatsService
from app.utils.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

# In-memory cache: (user_id_str, days, window_end_date_str) -> AIInsightsResponse dict
_insights_cache: dict[tuple[str, int, str], dict[str, Any]] = {}
INSIGHTS_RATE_LIMIT_PER_DAY = 5
SECONDS_PER_DAY = 86400


def _fallback_from_metrics(metrics: MetricsSummaryResponse) -> AIInsightsResponse:
    """Rules-only fallback: no made-up numbers; only from metrics."""
    summary = (
        f"Your volume over the last {metrics.period_days} days was {metrics.total_volume_kg:.0f} kg. "
        f"You trained {metrics.workouts_count} time(s) ({metrics.workouts_per_week:.1f} per week). "
    )
    if metrics.streak_days > 0:
        summary += f"Current streak: {metrics.streak_days} day(s). "
    if metrics.imbalance_hint:
        summary += metrics.imbalance_hint
    else:
        summary += "Consider adding one set to your main compound lifts next time."
    strengths = []
    if metrics.workouts_count > 0:
        strengths.append(f"Consistent training ({metrics.workouts_count} workout(s) in period)")
    if metrics.total_volume_kg > 0:
        strengths.append(f"Total volume: {metrics.total_volume_kg:.0f} kg")
    if not strengths:
        strengths.append("Ready to build a habit")
    gaps = []
    if metrics.imbalance_hint:
        gaps.append(metrics.imbalance_hint)
    if metrics.workouts_per_week < 2 and metrics.period_days >= 7:
        gaps.append("Try to hit at least 2 workouts per week for better progress")
    if not gaps:
        gaps.append("Keep progressive overload on main lifts")
    next_workout = [
        NextWorkoutItem(exercise_name="Compound lift (e.g. squat, bench, row)", sets_reps_guidance="3–4 sets of 6–10 reps"),
        NextWorkoutItem(exercise_name="Accessory or cardio", sets_reps_guidance="2–3 sets or 10–20 min"),
    ]
    return AIInsightsResponse(
        summary=summary[:400],
        strengths=strengths[:3],
        gaps=gaps[:3],
        next_workout=next_workout,
        progression_rule="Add weight or reps when you hit the top of your rep range for all sets.",
    )


def get_cached_insights(user_id: UUID, days: int, window_end: date) -> AIInsightsResponse | None:
    """Return cached insight if present."""
    key = (str(user_id), days, window_end.isoformat())
    raw = _insights_cache.get(key)
    if not raw:
        return None
    try:
        return AIInsightsResponse.model_validate(raw)
    except Exception:
        return None


def set_cached_insights(user_id: UUID, days: int, window_end: date, response: AIInsightsResponse) -> None:
    """Store in cache."""
    key = (str(user_id), days, window_end.isoformat())
    _insights_cache[key] = response.model_dump()


def get_insights(
    user_id: UUID,
    user_timezone: str,
    days: int,
    db: Session,
    request_id: str,
) -> tuple[AIInsightsResponse, bool, bool]:
    """
    Load metrics, check cache, rate limit, then generate or fallback.
    Returns (response, cache_hit, rate_limited).
    """
    stats_svc = StatsService(db)
    metrics = stats_svc.get_metrics_summary(user_id, user_timezone, days)
    tz = user_timezone or "UTC"
    window_end = stats_svc._get_today_date(tz)
    cached = get_cached_insights(user_id, days, window_end)
    if cached is not None:
        logger.info(
            "ai_insights cache_hit=true request_id=%s user_id=%s days=%s",
            request_id, user_id, days,
        )
        return (cached, True, False)
    today_str = window_end.isoformat()
    rate_key = f"ai_insights:{user_id}:{today_str}"
    count = check_rate_limit(rate_key, limit=INSIGHTS_RATE_LIMIT_PER_DAY, window_seconds=SECONDS_PER_DAY)
    if count > INSIGHTS_RATE_LIMIT_PER_DAY:
        logger.info(
            "ai_insights rate_limited request_id=%s user_id=%s days=%s",
            request_id, user_id, days,
        )
        raise ValueError("rate_limited")
    start = datetime.now(timezone.utc)
    if not settings.AI_ENABLED:
        out = _fallback_from_metrics(metrics)
        set_cached_insights(user_id, days, window_end, out)
        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        logger.info(
            "ai_insights cache_hit=false request_id=%s user_id=%s days=%s latency_ms=%s rate_limited=false",
            request_id, user_id, days, latency_ms,
        )
        return (out, False, False)
    llm = LLMService()
    metrics_dict = metrics.model_dump()
    try:
        if llm.bedrock_ready and llm._client and llm._model_daily:
            generated = _generate_insights_llm(llm, metrics_dict)
            if generated is not None:
                set_cached_insights(user_id, days, window_end, generated)
                latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
                logger.info(
                    "ai_insights cache_hit=false request_id=%s user_id=%s days=%s latency_ms=%s rate_limited=false",
                    request_id, user_id, days, latency_ms,
                )
                return (generated, False, False)
    except Exception as e:
        logger.warning("ai_insights LLM failed request_id=%s error=%s", request_id, e)
    out = _fallback_from_metrics(metrics)
    set_cached_insights(user_id, days, window_end, out)
    latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    logger.info(
        "ai_insights cache_hit=false fallback=true request_id=%s user_id=%s days=%s latency_ms=%s rate_limited=false",
        request_id, user_id, days, latency_ms,
    )
    return (out, False, False)


def _generate_insights_llm(llm: LLMService, metrics_dict: dict[str, Any]) -> AIInsightsResponse | None:
    """Call LLM (plain text); parse JSON into AIInsightsResponse; return None on failure."""
    system_prompt = (
        "You are a supportive fitness coach. Respond only with a single JSON object with exactly these keys: "
        "summary (string, max 400 chars), strengths (array of up to 3 strings), gaps (array of up to 3 strings), "
        "next_workout (array of objects with exercise_name and sets_reps_guidance, max 5 items), progression_rule (string, max 300 chars). "
        "No markdown, no code block wrapper. Use only the numbers from the metrics provided; do not invent numbers."
    )
    user_prompt = (
        "Based on this user's training metrics, write a brief insight: summary, 1-3 strengths, 1-3 gaps, "
        "suggested next_workout exercises with sets_reps_guidance, and one short progression_rule. "
        "Output only valid JSON.\n\n"
        f"Metrics: {json.dumps(metrics_dict, default=str)}"
    )
    text, _, _ = llm._invoke_plain_text(
        model_id=llm._model_daily,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    if not text or "{" not in text:
        return None
    start = text.index("{")
    depth = 0
    for i, c in enumerate(text[start:], start=start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
                if not isinstance(data, dict):
                    return None
                try:
                    return AIInsightsResponse(
                        summary=str(data.get("summary", ""))[:400],
                        strengths=[str(x) for x in (data.get("strengths") or [])][:3],
                        gaps=[str(x) for x in (data.get("gaps") or [])][:3],
                        next_workout=[
                            NextWorkoutItem(
                                exercise_name=str(x.get("exercise_name", ""))[:200],
                                sets_reps_guidance=str(x.get("sets_reps_guidance", ""))[:200],
                            )
                            for x in (data.get("next_workout") or [])[:10]
                        ],
                        progression_rule=str(data.get("progression_rule", ""))[:300],
                    )
                except Exception:
                    return None
    return None
