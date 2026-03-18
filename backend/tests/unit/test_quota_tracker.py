import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.core.quota_tracker import QuotaTracker, TempVIPManager


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.get.return_value = None
    r.pipeline.return_value = r
    r.execute.return_value = [10, 100, True, True]
    return r


class TestQuotaTracker:
    def test_get_usage_empty(self, mock_redis):
        tracker = QuotaTracker(mock_redis)
        daily, monthly = tracker.get_usage(user_id=1)
        assert daily == 0
        assert monthly == 0

    def test_get_usage_with_data(self, mock_redis):
        mock_redis.get.side_effect = [b"42", b"350"]
        tracker = QuotaTracker(mock_redis)
        daily, monthly = tracker.get_usage(user_id=1)
        assert daily == 42
        assert monthly == 350

    def test_consume_increments(self, mock_redis):
        mock_redis.execute.return_value = [15, 115, True, True]
        tracker = QuotaTracker(mock_redis)
        daily, monthly = tracker.consume(user_id=1, pages=5)
        assert daily == 15
        assert monthly == 115
        mock_redis.incrby.assert_called()

    def test_consume_sets_expiry(self, mock_redis):
        mock_redis.execute.return_value = [5, 5, True, True]
        tracker = QuotaTracker(mock_redis)
        tracker.consume(user_id=1, pages=5)
        # expire should be called twice (daily + monthly)
        assert mock_redis.expire.call_count == 2

    def test_reset_daily(self, mock_redis):
        tracker = QuotaTracker(mock_redis)
        tracker.reset_daily(user_id=1)
        mock_redis.delete.assert_called_once()

    def test_reset_monthly(self, mock_redis):
        tracker = QuotaTracker(mock_redis)
        tracker.reset_monthly(user_id=1)
        mock_redis.delete.assert_called_once()


class TestTempVIPManager:
    def test_grant_sets_key_with_ttl(self, mock_redis):
        mgr = TempVIPManager(mock_redis)
        until = datetime.now() + timedelta(hours=24)
        mgr.grant(user_id=1, until=until)
        mock_redis.setex.assert_called_once()

    def test_is_temp_vip_when_not_set(self, mock_redis):
        mock_redis.exists.return_value = 0
        mgr = TempVIPManager(mock_redis)
        assert mgr.is_temp_vip(1) is False

    def test_is_temp_vip_when_set(self, mock_redis):
        mock_redis.exists.return_value = 1
        mgr = TempVIPManager(mock_redis)
        assert mgr.is_temp_vip(1) is True

    def test_get_expiry(self, mock_redis):
        mock_redis.get.return_value = b"2026-03-20T00:00:00"
        mgr = TempVIPManager(mock_redis)
        assert mgr.get_expiry(1) == "2026-03-20T00:00:00"

    def test_get_expiry_none(self, mock_redis):
        mock_redis.get.return_value = None
        mgr = TempVIPManager(mock_redis)
        assert mgr.get_expiry(1) is None

    def test_revoke(self, mock_redis):
        mgr = TempVIPManager(mock_redis)
        mgr.revoke(1)
        mock_redis.delete.assert_called_once()
