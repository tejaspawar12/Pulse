"""Send push notifications via Expo Push API."""
import logging
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription
from app.models.user import User

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class PushService:
    """
    Send push notifications via Expo Push API.
    Expo tokens (ExponentPushToken[xxx]) must be sent via this API; Expo routes to APNs/FCM.
    """

    def send_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> tuple[bool, str | None]:
        """Send a single push notification. Returns (success, error_type). Caller can deactivate on DeviceNotRegistered."""
        payload = {
            "to": push_token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {},
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    EXPO_PUSH_URL,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                result = response.json()
                data_list = result.get("data", [])
                if not isinstance(data_list, list):
                    data_list = [data_list]
                if not data_list:
                    return True, None
                ticket = data_list[0]
                if ticket.get("status") == "error":
                    err = ticket.get("details", {}).get("error", "Unknown")
                    msg = ticket.get("message", "")
                    logger.warning("Expo push failed: %s - %s", err, msg)
                    return False, err
                return True, None
        except Exception as e:
            logger.error("Push notification failed: %s", type(e).__name__)
            return False, "Unknown"

    def send_to_user(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict | None,
        db: Session,
    ) -> None:
        """Send to all active push tokens for a user. Respects user.notifications_enabled. Deactivates dead tokens immediately on DeviceNotRegistered."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.notifications_enabled:
            return
        subscriptions = (
            db.query(PushSubscription)
            .filter(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
            )
            .all()
        )
        for sub in subscriptions:
            success, err = self.send_notification(sub.push_token, title, body, data)
            if not success:
                if err == "DeviceNotRegistered":
                    sub.is_active = False
                else:
                    sub.failed_count = (sub.failed_count or 0) + 1
                    if sub.failed_count >= 3:
                        sub.is_active = False
        db.commit()


push_service = PushService()
