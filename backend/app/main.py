import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config.settings import settings


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Phase 3: Add X-Request-Id to every response for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

# Import all models to ensure SQLAlchemy can resolve relationships
# This must happen before any routes are registered
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.models.training_plan import TrainingPlan  # noqa: F401 - Phase 2 Week 7
from app.models.weekly_plan_adjustment import WeeklyPlanAdjustment  # noqa: F401 - Phase 2 Week 7

app = FastAPI(title="Fitness API", version="1.0.0")

# Phase 3: Request ID for tracing (add early so all routes get it)
app.add_middleware(RequestIdMiddleware)

# CORS configuration (LOCKED - environment-based)
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in dev
        allow_credentials=False,  # Required when using "*" with credentials
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-DEV-USER-ID"],
    )
else:
    # Production CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # Add your production domains here
        allow_credentials=False,  # We use JWT in headers, not cookies
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-DEV-USER-ID"],
    )

@app.get("/")
def root():
    return {"message": "Fitness API v1", "status": "running"}

# Register routers
from app.api.v1 import (
    health,
    time,
    workouts,
    user,
    exercises,
    auth,
    demo,
    push,
    stats,
    metrics,
    ai,
    coach,
    accountability,
    reports,
    predictions,
    plan,
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(demo.router, prefix="/api/v1", tags=["demo"])
app.include_router(time.router, prefix="/api/v1", tags=["time"])
app.include_router(workouts.router, prefix="/api/v1", tags=["workouts"])
app.include_router(user.router, prefix="/api/v1", tags=["user"])
app.include_router(exercises.router, prefix="/api/v1", tags=["exercises"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(push.router, prefix="/api/v1", tags=["push"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(ai.router, prefix="/api/v1")
app.include_router(coach.router, prefix="/api/v1")
app.include_router(accountability.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(plan.router, prefix="/api/v1")