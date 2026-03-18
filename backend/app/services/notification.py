from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Web Push notification service for job completion."""

    def __init__(self, redis_client):
        self.r = redis_client

    def _subscription_key(self, user_id: int) -> str:
        return f"push_sub:{user_id}"

    def register_subscription(self, user_id: int, subscription: dict) -> None:
        """Store push subscription for a user."""
        self.r.set(self._subscription_key(user_id), json.dumps(subscription))

    def get_subscription(self, user_id: int) -> Optional[dict]:
        """Get stored push subscription."""
        data = self.r.get(self._subscription_key(user_id))
        if data:
            return json.loads(data)
        return None

    def notify_job_complete(self, user_id: int, job_id: int, filename: str) -> bool:
        """Send push notification for completed job."""
        sub = self.get_subscription(user_id)
        if not sub:
            logger.info(f"No push subscription for user {user_id}")
            return False

        # In production, use pywebpush to send the notification
        # For now, log it
        logger.info(f"Push notification: job {job_id} ({filename}) complete for user {user_id}")
        return True

    def notify_job_failed(self, user_id: int, job_id: int, error: str) -> bool:
        """Send push notification for failed job."""
        sub = self.get_subscription(user_id)
        if not sub:
            return False
        logger.info(f"Push notification: job {job_id} failed for user {user_id}: {error}")
        return True
