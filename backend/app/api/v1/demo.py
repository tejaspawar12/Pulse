"""
Demo login, seed, reset (single mode — always available).
POST /demo/login: log in as demo user (no credentials).
POST /demo/seed, POST /demo/reset: require X-DEMO-KEY when DEMO_KEY is set.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.config.settings import settings
from app.data.demo_workouts_data import DEMO_NAME_TO_LIBRARY_NORMALIZED, DEMO_WORKOUTS
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.schemas.auth import AuthOut
from app.schemas.user import UserOut
from app.services.auth_service import AuthService
from app.utils.enums import LifecycleStatus, CompletionStatus, SetType

router = APIRouter()


def _build_exercise_id_map(db: Session) -> dict[str, UUID]:
    """Build normalized_name -> exercise id (UUID) from exercise_library."""
    rows = db.query(ExerciseLibrary.normalized_name, ExerciseLibrary.id).all()
    return {norm: eid for norm, eid in rows}


def _resolve_exercise_id(demo_exercise_name: str, id_by_normalized: dict[str, UUID]) -> UUID | None:
    """Resolve demo exercise display name to library exercise id."""
    normalized = DEMO_NAME_TO_LIBRARY_NORMALIZED.get(demo_exercise_name)
    if normalized and normalized in id_by_normalized:
        return id_by_normalized[normalized]
    fallback = demo_exercise_name.strip().lower()
    return id_by_normalized.get(fallback)


def _seed_user_from_demo_data(db: Session, user_id: UUID) -> int:
    """Delete user's workouts, then create workouts from DEMO_WORKOUTS. Returns count added."""
    deleted = db.query(Workout).filter(Workout.user_id == user_id).delete()
    db.flush()
    id_by_norm = _build_exercise_id_map(db)
    if not id_by_norm:
        return 0
    added = 0
    for date_iso, workout_name, exercises_list in DEMO_WORKOUTS:
        start = datetime.fromisoformat(date_iso + "T12:00:00").replace(tzinfo=timezone.utc)
        end = start + timedelta(minutes=45)
        w = Workout(
            id=uuid4(),
            user_id=user_id,
            lifecycle_status=LifecycleStatus.FINALIZED.value,
            completion_status=CompletionStatus.COMPLETED.value,
            start_time=start,
            end_time=end,
            duration_minutes=45,
            name=workout_name,
        )
        db.add(w)
        db.flush()
        for order_index, (ex_name, sets_list) in enumerate(exercises_list):
            exercise_id = _resolve_exercise_id(ex_name, id_by_norm)
            if not exercise_id:
                continue
            we = WorkoutExercise(
                id=uuid4(),
                workout_id=w.id,
                exercise_id=exercise_id,
                order_index=order_index,
            )
            db.add(we)
            db.flush()
            for set_num, (reps, weight_lb) in enumerate(sets_list, start=1):
                db.add(
                    WorkoutSet(
                        id=uuid4(),
                        workout_exercise_id=we.id,
                        set_number=set_num,
                        set_type=SetType.WORKING.value,
                        reps=reps,
                        weight=float(weight_lb) if weight_lb else None,
                    )
                )
        added += 1
    db.commit()
    return added


def _require_demo_key(x_demo_key: str | None = Header(None, alias="X-DEMO-KEY")):
    """Require valid X-DEMO-KEY when DEMO_KEY is set (optional for local dev)."""
    if settings.DEMO_KEY and x_demo_key != settings.DEMO_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing X-DEMO-KEY")


@router.post("/demo/login", response_model=AuthOut)
def demo_login(db: Session = Depends(get_db)):
    """
    Log in as the demo user (no credentials). Creates demo user if not exists.
    Single mode: always available.
    """
    service = AuthService(db)
    try:
        user = service.get_or_create_demo_user()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    access_token, refresh_token = service.issue_tokens_for_user(user)
    expires_in = settings.JWT_EXPIRATION_DAYS * 24 * 60 * 60
    return AuthOut(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post("/demo/seed")
def demo_seed(
    db: Session = Depends(get_db),
    _key: None = Depends(_require_demo_key),
):
    """Seed demo user with curated workouts (Jan 14–Feb 4). Replaces any existing demo workouts."""
    service = AuthService(db)
    try:
        user = service.get_or_create_demo_user()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    added = _seed_user_from_demo_data(db, user.id)
    if added == 0:
        return {"message": "No exercises in library; seed skipped.", "workouts_added": 0}
    return {"message": "Demo seeded.", "workouts_added": added}


DEMO_EMAIL = "demo@example.com"


@router.post("/demo/seed-me")
def demo_seed_me(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """
    Seed the current user with sample workouts. Only for demo user (demo@example.com).
    Replaces any existing workouts with curated data. Use from app "Load sample workouts".
    """
    if (current_user.email or "").strip().lower() != DEMO_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the demo account can load sample workouts.",
        )
    added = _seed_user_from_demo_data(db, current_user.id)
    if added == 0:
        return {"message": "No exercises in library; seed skipped.", "workouts_added": 0}
    return {"message": "Sample workouts loaded.", "workouts_added": added}


@router.post("/demo/reset")
def demo_reset(
    db: Session = Depends(get_db),
    _key: None = Depends(_require_demo_key),
):
    """Delete all workouts for the demo user (clears History/Insights for Try Demo)."""
    service = AuthService(db)
    try:
        user = service.get_or_create_demo_user()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    deleted = db.query(Workout).filter(Workout.user_id == user.id).delete()
    db.commit()
    return {"message": "Demo reset.", "workouts_deleted": deleted}
