"""Push subscription and notification preference endpoints."""
from datetime import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.schemas.push import (
    PushSubscriptionRegisterIn,
    PushSubscriptionOut,
    NotificationPreferencesIn,
)
from app.services.push_service import push_service

router = APIRouter()


@router.get("/users/me/push-subscriptions", response_model=list[PushSubscriptionOut])
def list_my_subscriptions(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """List active push subscriptions for current user."""
    return (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.is_active == True,
        )
        .all()
    )


@router.post("/users/me/push-subscriptions", response_model=PushSubscriptionOut)
def register_push_subscription(
    data: PushSubscriptionRegisterIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Upsert by push_token (global unique). Reassign to current user if needed."""
    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.push_token == data.push_token)
        .first()
    )

    if existing:
        existing.user_id = current_user.id
        existing.platform = data.platform
        existing.is_active = True
        existing.failed_count = 0
        db.commit()
        db.refresh(existing)
        return existing

    sub = PushSubscription(
        user_id=current_user.id,
        push_token=data.push_token,
        platform=data.platform,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/users/me/push-subscriptions/{subscription_id}")
def unsubscribe_push(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Remove a push subscription (current user's only)."""
    sub = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.id == subscription_id,
            PushSubscription.user_id == current_user.id,
        )
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(sub)
    db.commit()
    return {"detail": "Unsubscribed"}


@router.patch("/users/me/notification-preferences")
def update_notification_preferences(
    data: NotificationPreferencesIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Update notifications_enabled and/or reminder_time for current user."""
    if data.notifications_enabled is not None:
        current_user.notifications_enabled = data.notifications_enabled
    if data.reminder_time is not None:
        if data.reminder_time == "":
            current_user.reminder_time = None
        else:
            parts = data.reminder_time.strip().split(":")
            if len(parts) >= 2:
                h, m = int(parts[0]), int(parts[1])
                current_user.reminder_time = time(hour=h, minute=m)
    db.commit()
    db.refresh(current_user)
    return {"detail": "Updated"}


@router.post("/users/me/push-subscriptions/test-send")
def send_test_notification(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Send a test push to current user's devices."""
    push_service.send_to_user(
        current_user.id,
        title="Test",
        body="This is a test notification from Fitness Coach.",
        data={"type": "test"},
        db=db,
    )
    return {"detail": "Test notification sent"}
