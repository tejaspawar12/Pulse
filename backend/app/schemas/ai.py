"""Phase 3 — AI insights response schema (GET /ai/insights)."""
from pydantic import BaseModel, Field


class NextWorkoutItem(BaseModel):
    """One suggested exercise for next workout."""
    exercise_name: str = Field(..., max_length=200)
    sets_reps_guidance: str = Field(..., max_length=200)


class AIInsightsResponse(BaseModel):
    """Schema-validated response for GET /api/v1/ai/insights."""
    summary: str = Field(..., max_length=400)
    strengths: list[str] = Field(..., max_length=3)
    gaps: list[str] = Field(..., max_length=3)
    next_workout: list[NextWorkoutItem] = Field(..., max_length=10)
    progression_rule: str = Field(..., max_length=300)
