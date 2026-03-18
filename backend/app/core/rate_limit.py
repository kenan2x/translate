from __future__ import annotations

from typing import Optional

import redis


class RateLimiter:
    """Sliding window rate limiter using Redis."""

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    def check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is allowed. Returns True if allowed."""
        import time

        now = time.time()
        pipe = self.r.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry on the set
        pipe.expire(key, window_seconds)
        results = pipe.execute()

        current_count = results[1]
        return current_count < max_requests

    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> int:
        """Get remaining requests in current window."""
        import time

        now = time.time()
        self.r.zremrangebyscore(key, 0, now - window_seconds)
        current = self.r.zcard(key)
        return max(0, max_requests - current)


# Default limits
UPLOAD_RATE_LIMIT = 5  # 5 uploads per minute
UPLOAD_RATE_WINDOW = 60  # 60 seconds
