"""
Predictions API: transformation timeline latest and history (Phase 2 Week 6).
Single mode: all authenticated users (including demo) have access.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.models.transformation_prediction import TransformationPrediction
from app.schemas.prediction import TransformationPredictionOut
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/transformation/latest", response_model=TransformationPredictionOut)
def get_transformation_latest(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    recompute: bool = Query(False, description="Recompute with current goal and consistency"),
):
    """Latest transformation prediction. If none exists (or recompute=True), compute on demand and return."""
    if not recompute:
        pred = (
            db.query(TransformationPrediction)
            .filter(TransformationPrediction.user_id == current_user.id)
            .order_by(desc(TransformationPrediction.computed_at))
            .first()
        )
        if pred:
            return pred
    prediction_svc = PredictionService(db)
    pred = prediction_svc.compute_prediction(current_user.id)
    return pred


@router.get("/transformation/history")
def get_transformation_history(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    limit: int = Query(12, ge=1, le=50, description="Max predictions to return"),
):
    """Paginated history (computed_at desc). Available to all authenticated users."""
    preds = (
        db.query(TransformationPrediction)
        .filter(TransformationPrediction.user_id == current_user.id)
        .order_by(desc(TransformationPrediction.computed_at))
        .limit(limit)
        .all()
    )
    return [TransformationPredictionOut.model_validate(p) for p in preds]
