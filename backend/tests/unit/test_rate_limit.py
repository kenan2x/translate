from unittest.mock import MagicMock

from app.core.rate_limit import RateLimiter, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW


def test_check_allows_under_limit():
    mock_redis = MagicMock()
    pipe = MagicMock()
    pipe.execute.return_value = [0, 2, True, True]  # zremrangebyscore, zcard=2, zadd, expire
    mock_redis.pipeline.return_value = pipe

    limiter = RateLimiter(mock_redis)
    assert limiter.check("test:key", max_requests=5, window_seconds=60) is True


def test_check_blocks_over_limit():
    mock_redis = MagicMock()
    pipe = MagicMock()
    pipe.execute.return_value = [0, 5, True, True]  # zcard=5 (at limit)
    mock_redis.pipeline.return_value = pipe

    limiter = RateLimiter(mock_redis)
    assert limiter.check("test:key", max_requests=5, window_seconds=60) is False


def test_get_remaining():
    mock_redis = MagicMock()
    mock_redis.zremrangebyscore.return_value = 0
    mock_redis.zcard.return_value = 3

    limiter = RateLimiter(mock_redis)
    remaining = limiter.get_remaining("test:key", max_requests=5, window_seconds=60)
    assert remaining == 2


def test_get_remaining_at_zero():
    mock_redis = MagicMock()
    mock_redis.zremrangebyscore.return_value = 0
    mock_redis.zcard.return_value = 10

    limiter = RateLimiter(mock_redis)
    remaining = limiter.get_remaining("test:key", max_requests=5, window_seconds=60)
    assert remaining == 0


def test_default_limits():
    assert UPLOAD_RATE_LIMIT == 5
    assert UPLOAD_RATE_WINDOW == 60
