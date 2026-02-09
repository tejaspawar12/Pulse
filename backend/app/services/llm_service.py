"""
LLM service: Bedrock Converse for daily coach message (Phase 2 Week 5 Day 3).
Sync only; no async. Singleton at module load.
Grounded to user data only; anti-hallucination prompts and post-check.
"""
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import boto3
from botocore.config import Config
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.config.settings import settings
from app.models.llm_usage_daily import LLMUsageDaily

logger = logging.getLogger(__name__)

# Expected JSON shape from model (no fake fallback)
COACH_MESSAGE_JSON_KEYS = {"coach_message", "quick_replies", "one_action_step"}


class CoachMessageOutput(BaseModel):
    coach_message: str = Field(..., min_length=1)
    quick_replies: list[str] = Field(..., min_length=1, max_length=5)
    one_action_step: str = Field(..., min_length=1)


def _extract_json_object(text: str) -> Optional[dict[str, Any]]:
    """
    Extract first complete {...} from text using bracket balance.
    Returns None if not found or invalid JSON.
    """
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
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _coach_message_grounding_check(coach_message: str, facts_json: dict[str, Any]) -> bool:
    """
    Return True if every number in coach_message appears in the serialized facts (grounded).
    If coach_message has no numbers, return True. Used to catch invented stats.
    """
    facts_str = json.dumps(facts_json, default=str)
    # Extract contiguous digits (integers) from message; ignore very short (e.g. single 0)
    numbers_in_message = re.findall(r"\d+", coach_message)
    for num_str in numbers_in_message:
        if num_str not in facts_str:
            return False
    return True


def _apply_coach_grounding_fallback(
    result: dict[str, Any], facts_json: dict[str, Any]
) -> dict[str, Any]:
    """
    If coach_message contains numbers not in facts_json, replace message with safe fallback.
    Keeps quick_replies and one_action_step unchanged.
    """
    msg = result.get("coach_message") or ""
    if _coach_message_grounding_check(msg, facts_json):
        return result
    logger.warning(
        "Coach message failed grounding check (numbers not in facts); replacing with safe fallback"
    )
    fallback = (result.get("one_action_step") or "").strip()
    if not fallback:
        fallback = "Stay consistent with your plan today."
    result = dict(result)
    result["coach_message"] = fallback
    return result


def _validate_coach_output(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Validate and normalize to CoachMessageOutput shape; return dict or None."""
    if not data or not isinstance(data, dict):
        return None
    if not COACH_MESSAGE_JSON_KEYS.issubset(data.keys()):
        return None
    try:
        out = CoachMessageOutput(
            coach_message=str(data["coach_message"]).strip(),
            quick_replies=[str(x).strip() for x in data["quick_replies"] if x],
            one_action_step=str(data["one_action_step"]).strip(),
        )
    except Exception:
        return None
    if not out.quick_replies:
        return None
    return {
        "coach_message": out.coach_message,
        "quick_replies": out.quick_replies,
        "one_action_step": out.one_action_step,
    }


class LLMService:
    """
    Bedrock Converse for coach message. Sync only.
    If Bedrock is unavailable at startup, bedrock_ready=False; coach returns "unavailable".
    """

    def __init__(self) -> None:
        self.bedrock_ready = False
        self._client = None
        self._model_daily: Optional[str] = None
        self._model_lite: Optional[str] = None
        if not settings.BEDROCK_MODEL_ID_DAILY:
            logger.warning("BEDROCK_MODEL_ID_DAILY not set; coach AI disabled.")
            return
        self._model_daily = settings.BEDROCK_MODEL_ID_DAILY
        self._model_lite = settings.BEDROCK_MODEL_ID_LITE
        try:
            config = Config(
                connect_timeout=5,
                read_timeout=settings.BEDROCK_TIMEOUT_SECONDS,
                retries={"max_attempts": 0},
            )
            # Pass credentials from Settings (.env) so boto3 uses them; otherwise it may use
            # a different source (e.g. ~/.aws/credentials) and trigger UnrecognizedClientException.
            client_kw: dict[str, Any] = {
                "service_name": "bedrock-runtime",
                "region_name": settings.AWS_REGION,
                "config": config,
            }
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                client_kw["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                client_kw["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self._client = boto3.client(**client_kw)
            # Lightweight validation: Converse with minimal prompt (or skip and set ready)
            self.bedrock_ready = True
            logger.info(
                "Bedrock ready: region=%s, model_daily=%s",
                settings.AWS_REGION,
                self._model_daily,
            )
        except Exception as e:
            logger.exception("Bedrock init failed: %s", e)
            self._client = None
            self.bedrock_ready = False

    def generate_coach_message(
        self,
        user_id: UUID,
        facts_json: dict[str, Any],
        usage_date: date,
        db: Session,
    ) -> dict[str, Any]:
        """
        Generate today's coach message via Bedrock. Returns dict with 'source' key:
        - source "ai": coach_message, quick_replies, one_action_step
        - source "unavailable": retry_after_seconds (no fake message)
        """
        if not self.bedrock_ready or not self._client or not self._model_daily:
            return {"source": "unavailable", "retry_after_seconds": 60}

        system_prompt = (
            "You are a supportive fitness coach. You have full visibility into the user's data: "
            "recent_workouts (date, duration, volume, exercises), recent_commitments, training_plan, "
            "last_weekly_report, and metrics.\n\n"
            "CRITICAL - Grounding rules:\n"
            "- Use ONLY the data provided. Do not invent any workout dates, exercise names, volumes, or stats.\n"
            "- Every number or fact in your message MUST come from the provided data. If you cannot find it in the data, do not say it.\n"
            "- If recent_workouts is empty or the user has no recent activity, do NOT mention specific exercises or volumes. Refer only to their context (new/returning/active) and goals.\n"
            "- Do not make up motivational stories or generic advice that is not tied to their data. Be specific only when the data supports it.\n\n"
            "Respond only with a single JSON object "
            "with exactly these keys: coach_message (string), quick_replies (array of 2-4 short strings), "
            "one_action_step (string). No markdown, no code block wrapper, no explanation outside the JSON.\n\n"
            "Tailor your message to user_context:\n"
            "- new: User has no or almost no workout history. Welcome them, suggest a small first step (e.g. 1-2 workouts this week). Do NOT say they have been inconsistent or that it has been tough to stay consistent.\n"
            "- returning: User had workouts in the past but has been inactive for over 30 days. Welcome them back warmly, ease them in, no guilt. Do NOT say they have been inconsistent lately.\n"
            "- active: User has recent activity. Use their metrics, recent_workouts, and focus (consistency, momentum, etc.) as usual."
        )
        recent_workouts = facts_json.get("recent_workouts") or []
        no_workouts_note = (
            " Note: recent_workouts is empty — do not mention specific exercises or volumes; only refer to context and goals."
            if not recent_workouts else ""
        )
        user_prompt = (
            "Based on this user data, write a brief daily coach message and one actionable step. "
            "Match the tone to user_context (new / returning / active). Be specific when active; when new or returning, be welcoming and avoid guilt. "
            "Use only numbers and facts that appear in the data below."
            f"{no_workouts_note} Output only valid JSON.\n\n"
            f"Data: {json.dumps(facts_json, default=str)}"
        )

        # Level 1: primary model (use coach temperature for grounding)
        result = self._invoke(
            model_id=self._model_daily,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            use_lite=False,
            temperature=settings.COACH_TEMPERATURE,
            top_p=settings.COACH_TOP_P,
        )
        if result.get("source") == "ai":
            result = _apply_coach_grounding_fallback(result, facts_json)
            self._log_usage(
                user_id=user_id,
                usage_date=usage_date,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                db=db,
            )
            return result

        # Retry once with shorter prompt (valid JSON only)
        if result.get("source") == "unavailable":
            short_prompt = (
                "Respond with a single JSON object: coach_message (string), "
                "quick_replies (array of 2-4 strings), one_action_step (string). Nothing else. Use only data provided.\n\n"
                f"Data: {json.dumps(facts_json, default=str)[:1500]}"
            )
            result = self._invoke(
                model_id=self._model_daily,
                system_prompt="Output only valid JSON. No markdown. Do not invent any numbers or stats.",
                user_prompt=short_prompt,
                use_lite=False,
                temperature=settings.COACH_TEMPERATURE,
                top_p=settings.COACH_TOP_P,
            )
            if result.get("source") == "ai":
                result = _apply_coach_grounding_fallback(result, facts_json)
                self._log_usage(
                    user_id=user_id,
                    usage_date=usage_date,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    db=db,
                )
                return result

        # Level 2: retry with lite model
        if self._model_lite:
            result_lite = self._invoke(
                model_id=self._model_lite,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                use_lite=True,
                temperature=settings.COACH_TEMPERATURE,
                top_p=settings.COACH_TOP_P,
            )
            if result_lite.get("source") == "ai":
                result_lite["ai_lite_used"] = True
                result_lite = _apply_coach_grounding_fallback(result_lite, facts_json)
                self._log_usage(
                    user_id=user_id,
                    usage_date=usage_date,
                    input_tokens=result_lite.get("input_tokens", 0),
                    output_tokens=result_lite.get("output_tokens", 0),
                    db=db,
                )
                return result_lite

        # Level 3: unavailable
        return {"source": "unavailable", "retry_after_seconds": 60}

    def generate_weekly_narrative(
        self,
        user_id: UUID,
        diagnosis_json: dict[str, Any],
        db: Session,
    ) -> Optional[str]:
        """
        Write a short 2–3 sentence weekly training summary. Be encouraging and specific.
        Returns plain text or None on failure. Logs usage to LLMUsageDaily (report_calls).
        """
        if not self.bedrock_ready or not self._client or not self._model_daily:
            return None
        usage_date = datetime.now(timezone.utc).date()
        system_prompt = (
            "You are a supportive fitness coach. Write a short 2–3 sentence weekly training "
            "summary for the user. Be encouraging and specific to the data. Output only plain "
            "text, no JSON, no markdown."
        )
        user_prompt = (
            "Based on this weekly diagnosis, write a brief encouraging summary (2–3 sentences).\n\n"
            f"Data: {json.dumps(diagnosis_json, default=str)}"
        )
        text_out, input_tok, output_tok = self._invoke_plain_text(
            model_id=self._model_daily,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        if text_out is None or not text_out.strip():
            return None
        self._log_usage(
            user_id=user_id,
            usage_date=usage_date,
            input_tokens=input_tok,
            output_tokens=output_tok,
            db=db,
            coach_calls=0,
            report_calls=1,
        )
        return text_out.strip()

    def _invoke_plain_text(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[Optional[str], int, int]:
        """Call Converse and return (raw_text, input_tokens, output_tokens). No JSON parsing."""
        if not self._client:
            return (None, 0, 0)
        try:
            response = self._client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": min(512, settings.BEDROCK_MAX_TOKENS),
                    "temperature": settings.BEDROCK_TEMPERATURE,
                    "topP": settings.BEDROCK_TOP_P,
                },
            )
        except Exception as e:
            logger.warning(
                "Bedrock Converse failed (model=%s): %s: %s",
                model_id,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            return (None, 0, 0)
        usage = response.get("usage", {})
        input_tok = usage.get("inputTokens", 0) or 0
        output_tok = usage.get("outputTokens", 0) or 0
        text = ""
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                text += block["text"]
        return (text if text else None, input_tok, output_tok)

    def generate_chat_reply(
        self,
        user_id: UUID,
        facts_json: dict[str, Any],
        history: list[dict[str, str]],
        user_message: str,
        usage_date: date,
        db: Session,
    ) -> tuple[Optional[str], int, int]:
        """
        Generate coach chat reply using Converse with message history.
        history: list of {"role": "user"|"assistant", "content": "..."}.
        Returns (reply_text, input_tokens, output_tokens) or (None, 0, 0) on failure.
        Uses lite model when available to keep cost down.
        """
        if not self.bedrock_ready or not self._client:
            return (None, 0, 0)
        model_id = self._model_lite or self._model_daily
        if not model_id:
            return (None, 0, 0)
        system_prompt = (
            "You are a supportive fitness coach. The user can ask you anything about fitness, workouts, body transformation, "
            "nutrition, recovery, technique, or their own training. Answer helpfully like a real human coach.\n\n"
            "You have context about THIS user below (recent_workouts, training_plan, metrics, weekly focus). "
            "When your answer involves this user's history, plan, progress, or numbers (e.g. what they did last week, "
            "what workout to do next, their consistency), use ONLY the context below. Do not invent or assume anything "
            "about this user—no made-up workouts, dates, or stats. For general fitness questions (e.g. 'is training when sore ok?', "
            "'how much protein?'), use your knowledge and answer normally.\n\n"
            "Rule: General fitness advice = use your knowledge. Anything specific to this user = only from the context below.\n\n"
            f"User context: {json.dumps(facts_json, default=str)}"
        )
        messages: list[dict[str, Any]] = []
        for turn in history:
            role = turn.get("role") or "user"
            content = (turn.get("content") or "").strip()
            if content and role in ("user", "assistant"):
                messages.append({"role": role, "content": [{"text": content}]})
        user_text = (user_message or "").strip()
        if not user_text:
            return (None, 0, 0)
        # Remind to ground user-specific claims only (does not block general answers)
        user_text_with_reminder = (
            user_text + "\n\n[When referring to this user's workouts, plan, or progress, use only the context in the system message.]"
        )
        messages.append({"role": "user", "content": [{"text": user_text_with_reminder}]})
        try:
            response = self._client.converse(
                modelId=model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": min(512, settings.BEDROCK_MAX_TOKENS),
                    "temperature": settings.COACH_TEMPERATURE,
                    "topP": settings.COACH_TOP_P,
                },
            )
        except Exception as e:
            logger.warning(
                "Bedrock Converse chat failed (model=%s): %s: %s",
                model_id,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            return (None, 0, 0)
        usage = response.get("usage", {})
        input_tok = usage.get("inputTokens", 0) or 0
        output_tok = usage.get("outputTokens", 0) or 0
        text = ""
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                text += block["text"]
        reply = (text or "").strip() or None
        if reply:
            self._log_usage(
                user_id=user_id,
                usage_date=usage_date,
                input_tokens=input_tok,
                output_tokens=output_tok,
                db=db,
                coach_calls=1,
                report_calls=0,
            )
        return (reply, input_tok, output_tok)

    def _invoke(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        use_lite: bool,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> dict[str, Any]:
        """Call Converse; return parsed result dict or error state. No stopSequences."""
        max_tokens = settings.BEDROCK_MAX_TOKENS if not use_lite else min(512, settings.BEDROCK_MAX_TOKENS)
        temp = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
        top = top_p if top_p is not None else settings.BEDROCK_TOP_P
        try:
            response = self._client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temp,
                    "topP": top,
                },
            )
        except Exception as e:
            logger.warning(
                "Bedrock Converse failed (model=%s): %s: %s",
                model_id,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            return {"source": "unavailable", "retry_after_seconds": 60}

        usage = response.get("usage", {})
        input_tokens = usage.get("inputTokens", 0) or 0
        output_tokens = usage.get("outputTokens", 0) or 0
        text = ""
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                text += block["text"]

        parsed = _extract_json_object(text)
        validated = _validate_coach_output(parsed) if parsed else None
        if not validated:
            logger.warning(
                "Bedrock returned invalid coach JSON (model=%s). text_len=%s preview=%s",
                model_id,
                len(text),
                (text[:200] + "..." if len(text) > 200 else text) if text else "(empty)",
            )
            return {"source": "unavailable", "retry_after_seconds": 60}
        if validated:
            return {
                "source": "ai",
                "coach_message": validated["coach_message"],
                "quick_replies": validated["quick_replies"],
                "one_action_step": validated["one_action_step"],
                "model_id": model_id,
                "ai_lite_used": use_lite,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        return {"source": "unavailable", "retry_after_seconds": 60}

    def generate_workout_summary(
        self,
        user_id: UUID,
        workout_payload: dict[str, Any],
        usage_date: date,
        db: Session,
    ) -> tuple[Optional[str], int, int]:
        """
        Generate a short (2–4 sentence) AI summary for a single workout.
        workout_payload: dict with date, duration_minutes, exercises (list of {name, sets: [{weight, reps, set_type}]}).
        Returns (summary_text, input_tokens, output_tokens) or (None, 0, 0) on failure.
        Uses lite model when available to keep cost down.
        """
        if not self.bedrock_ready or not self._client:
            return (None, 0, 0)
        model_id = self._model_lite or self._model_daily
        if not model_id:
            return (None, 0, 0)
        system_prompt = (
            "You are a supportive fitness coach. Given workout data, write 2–4 short sentences: "
            "what the user did (exercises, volume), and one practical tip or encouragement. "
            "Use only the data provided; do not invent numbers. Output plain text only, no JSON or markdown."
        )
        user_prompt = (
            "Write a brief workout summary (2–4 sentences) based on this data. "
            "Be specific about exercises and effort; end with one short tip or encouragement.\n\n"
            f"Data: {json.dumps(workout_payload, default=str)}"
        )
        text_out, input_tok, output_tok = self._invoke_plain_text(
            model_id=model_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        summary = (text_out or "").strip() or None
        if summary:
            self._log_usage(
                user_id=user_id,
                usage_date=usage_date,
                input_tokens=input_tok,
                output_tokens=output_tok,
                db=db,
                coach_calls=0,
                report_calls=0,
                summary_calls=1,
            )
        return (summary, input_tok, output_tok)

    def _log_usage(
        self,
        user_id: UUID,
        usage_date: date,
        input_tokens: int,
        output_tokens: int,
        db: Session,
        coach_calls: int = 1,
        report_calls: int = 0,
        summary_calls: int = 0,
    ) -> None:
        """Upsert LLMUsageDaily: add tokens and increment coach_calls, report_calls, summary_calls."""
        total = input_tokens + output_tokens
        stmt = insert(LLMUsageDaily).values(
            id=uuid4(),
            user_id=user_id,
            usage_date=usage_date,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            coach_calls=coach_calls,
            report_calls=report_calls,
            plan_calls=0,
            summary_calls=summary_calls,
            updated_at=datetime.now(timezone.utc),
        ).on_conflict_do_update(
            index_elements=["user_id", "usage_date"],
            set_={
                "input_tokens": LLMUsageDaily.input_tokens + input_tokens,
                "output_tokens": LLMUsageDaily.output_tokens + output_tokens,
                "total_tokens": LLMUsageDaily.total_tokens + total,
                "coach_calls": LLMUsageDaily.coach_calls + coach_calls,
                "report_calls": LLMUsageDaily.report_calls + report_calls,
                "summary_calls": LLMUsageDaily.summary_calls + summary_calls,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        db.execute(stmt)
        db.flush()


# Singleton
llm_service = LLMService()
