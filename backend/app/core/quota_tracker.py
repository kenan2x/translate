from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple

import redis


class QuotaTracker:
    """Track quota usage via Redis (fast) with DB persistence."""

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    def _daily_key(self, user_id: int, d: Optional[date] = None) -> str:
        d = d or date.today()
        return f"quota:daily:{user_id}:{d.isoformat()}"

    def _monthly_key(self, user_id: int, d: Optional[date] = None) -> str:
        d = d or date.today()
        return f"quota:monthly:{user_id}:{d.year}-{d.month:02d}"

    def get_usage(self, user_id: int) -> Tuple[int, int]:
        """Get (daily_used, monthly_used) page counts."""
        daily = self.r.get(self._daily_key(user_id))
        monthly = self.r.get(self._monthly_key(user_id))
        return int(daily or 0), int(monthly or 0)

    def consume(self, user_id: int, pages: int) -> Tuple[int, int]:
        """Increment quota counters. Returns (new_daily, new_monthly)."""
        daily_key = self._daily_key(user_id)
        monthly_key = self._monthly_key(user_id)

        pipe = self.r.pipeline()
        pipe.incrby(daily_key, pages)
        pipe.incrby(monthly_key, pages)

        # Set expiry: daily expires at midnight, monthly at month end
        today = date.today()
        tomorrow = today + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time())
        daily_ttl = int((midnight - datetime.now()).total_seconds()) + 1

        # Monthly: expire at end of month + 1 day buffer
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        monthly_ttl = int((datetime.combine(next_month, datetime.min.time()) - datetime.now()).total_seconds()) + 1

        pipe.expire(daily_key, daily_ttl)
        pipe.expire(monthly_key, monthly_ttl)
        results = pipe.execute()

        return int(results[0]), int(results[1])

    def reset_daily(self, user_id: int) -> None:
        """Reset daily quota (called by Celery beat at midnight)."""
        self.r.delete(self._daily_key(user_id))

    def reset_monthly(self, user_id: int) -> None:
        """Reset monthly quota (called by Celery beat on 1st)."""
        self.r.delete(self._monthly_key(user_id))


class TempVIPManager:
    """Manage temporary VIP status with TTL."""

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    def _key(self, user_id: int) -> str:
        return f"temp_vip:{user_id}"

    def grant(self, user_id: int, until: datetime) -> None:
        """Grant temporary VIP until specified datetime."""
        ttl = int((until - datetime.now()).total_seconds())
        if ttl > 0:
            self.r.setex(self._key(user_id), ttl, until.isoformat())

    def is_temp_vip(self, user_id: int) -> bool:
        """Check if user has active temporary VIP."""
        return self.r.exists(self._key(user_id)) > 0

    def get_expiry(self, user_id: int) -> Optional[str]:
        """Get VIP expiry datetime string, or None."""
        val = self.r.get(self._key(user_id))
        return val.decode() if val else None

    def revoke(self, user_id: int) -> None:
        """Remove temporary VIP."""
        self.r.delete(self._key(user_id))
