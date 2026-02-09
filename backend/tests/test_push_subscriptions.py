"""
Tests for push subscription and notification preference endpoints.
Phase 2 Week 2.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.push_subscription import PushSubscription


@pytest.fixture
def test_user_with_notifications(db: Session) -> User:
    """Create a test user (notifications_enabled and reminder_time from model defaults)."""
    user = User(
        id=uuid4(),
        email="pushuser@example.com",
        password_hash="hashed",
        units="kg",
        timezone="UTC",
        notifications_enabled=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def push_auth_headers(test_user_with_notifications: User) -> dict:
    """Auth headers for the push test user."""
    return {"X-DEV-USER-ID": str(test_user_with_notifications.id)}


def test_register_push_token(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """POST register push token returns 200 and subscription."""
    response = client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[abc123]", "platform": "android"},
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["platform"] == "android"
    assert data["is_active"] is True
    assert data["user_id"] == str(test_user_with_notifications.id)
    assert "id" in data


def test_register_same_token_again(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """Register same token again returns 200 and updates subscription."""
    client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[same]", "platform": "ios"},
        headers=push_auth_headers,
    )
    response = client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[same]", "platform": "android"},
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["platform"] == "android"
    assert data["is_active"] is True


def test_list_my_subscriptions(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """GET my push subscriptions returns list."""
    client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[list1]", "platform": "android"},
        headers=push_auth_headers,
    )
    response = client.get("/api/v1/users/me/push-subscriptions", headers=push_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all("platform" in s and "is_active" in s and "id" in s for s in data)


def test_unsubscribe_push(client: TestClient, push_auth_headers: dict, db: Session, test_user_with_notifications: User):
    """DELETE subscription returns 200 and removes subscription."""
    r = client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[delete-me]", "platform": "ios"},
        headers=push_auth_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    sub_id = r.json()["id"]
    response = client.delete(
        f"/api/v1/users/me/push-subscriptions/{sub_id}",
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    list_resp = client.get("/api/v1/users/me/push-subscriptions", headers=push_auth_headers)
    ids = [s["id"] for s in list_resp.json()]
    assert sub_id not in ids


def test_unsubscribe_404(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """DELETE non-existent subscription returns 404."""
    response = client.delete(
        f"/api/v1/users/me/push-subscriptions/{uuid4()}",
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_notification_preferences(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """PATCH notification preferences returns 200."""
    response = client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"notifications_enabled": False},
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    response2 = client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"notifications_enabled": True, "reminder_time": "09:00"},
        headers=push_auth_headers,
    )
    assert response2.status_code == status.HTTP_200_OK


def test_reminder_time_validation_invalid(client: TestClient, push_auth_headers: dict):
    """PATCH with invalid reminder_time format returns 422."""
    response = client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"reminder_time": "25:99"},
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reminder_time_clear(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """PATCH reminder_time empty string clears value."""
    client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"reminder_time": "09:00"},
        headers=push_auth_headers,
    )
    response = client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"reminder_time": ""},
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_push_endpoints_require_auth(client: TestClient):
    """Unauthenticated requests to push endpoints return 401."""
    r1 = client.get("/api/v1/users/me/push-subscriptions")
    assert r1.status_code == status.HTTP_401_UNAUTHORIZED
    r2 = client.post(
        "/api/v1/users/me/push-subscriptions",
        json={"push_token": "ExponentPushToken[x]", "platform": "android"},
    )
    assert r2.status_code == status.HTTP_401_UNAUTHORIZED
    r3 = client.patch(
        "/api/v1/users/me/notification-preferences",
        json={"notifications_enabled": True},
    )
    assert r3.status_code == status.HTTP_401_UNAUTHORIZED


def test_test_send_endpoint(client: TestClient, push_auth_headers: dict, test_user_with_notifications: User):
    """POST test-send returns 200 (sending is best-effort)."""
    response = client.post(
        "/api/v1/users/me/push-subscriptions/test-send",
        headers=push_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
