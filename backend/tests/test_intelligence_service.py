"""
Tests for IntelligenceService (Phase 2 Week 5 Day 2).
"""
import pytest
from uuid import uuid4

from app.services.intelligence_service import IntelligenceService
from app.models.user import User
from app.models.user_coach_profile import UserCoachProfile
from app.models.user_behavior_metrics import UserBehaviorMetrics


def test_compute_metrics_no_workouts(db, test_user):
    """With no workouts and no profile, metrics use defaults and no mistake."""
    service = IntelligenceService(db)
    metrics = service.compute_metrics(test_user.id)
    db.commit()

    row = (
        db.query(UserBehaviorMetrics)
        .filter(
            UserBehaviorMetrics.user_id == test_user.id,
        )
        .first()
    )
    assert row is not None
    assert row.workouts_last_7_days == 0
    assert row.workouts_last_14_days == 0
    assert row.consistency_score is not None
    assert row.dropout_risk in ("low", "medium", "high")
    assert row.adherence_type in ("consistent", "weekend_warrior", "sporadic")
    # No workouts -> inconsistent_training_days (first rule)
    assert row.primary_training_mistake_key == "inconsistent_training_days"
    assert row.weekly_focus_key == "hit_target_days"


def test_compute_metrics_with_profile(db, test_user):
    """With coach profile, target_days and target_minutes are used."""
    profile = UserCoachProfile(
        user_id=test_user.id,
        target_days_per_week=4,
        target_session_minutes=45,
        experience_level="intermediate",
    )
    db.add(profile)
    db.commit()

    service = IntelligenceService(db)
    metrics = service.compute_metrics(test_user.id)
    db.commit()

    row = (
        db.query(UserBehaviorMetrics)
        .filter(
            UserBehaviorMetrics.user_id == test_user.id,
        )
        .first()
    )
    assert row is not None
    # Consistency score uses target 4 -> expected 8 in 2 weeks; 0 workouts -> low score
    assert row.consistency_score is not None
    assert 0 <= row.consistency_score <= 100


def test_compute_metrics_upsert_same_date(db, test_user):
    """Calling compute_metrics twice for same user/date updates the same row."""
    service = IntelligenceService(db)
    service.compute_metrics(test_user.id)
    db.commit()

    count_before = db.query(UserBehaviorMetrics).filter(UserBehaviorMetrics.user_id == test_user.id).count()
    assert count_before == 1

    service2 = IntelligenceService(db)
    service2.compute_metrics(test_user.id)
    db.commit()

    count_after = db.query(UserBehaviorMetrics).filter(UserBehaviorMetrics.user_id == test_user.id).count()
    assert count_after == 1


def test_user_not_found_raises(db):
    """compute_metrics raises ValueError for unknown user_id."""
    service = IntelligenceService(db)
    with pytest.raises(ValueError, match="User not found"):
        service.compute_metrics(uuid4())
