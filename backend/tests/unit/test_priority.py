import time
import pytest

from app.core.priority import (
    QueueEntry,
    get_priority_for_tier,
    sort_queue,
    get_queue_position,
    STARVATION_THRESHOLD_SECONDS,
)
from app.models.user import UserTier


def test_get_priority_for_tiers():
    assert get_priority_for_tier(UserTier.ADMIN) == 0
    assert get_priority_for_tier(UserTier.VIP) == 1
    assert get_priority_for_tier(UserTier.POWER_USER) == 2
    assert get_priority_for_tier(UserTier.STANDARD) == 3


def test_vip_before_standard():
    now = time.time()
    entries = [
        QueueEntry(job_id=1, user_id=10, user_tier="standard", priority=3, queued_at=now),
        QueueEntry(job_id=2, user_id=20, user_tier="vip", priority=1, queued_at=now),
    ]
    sorted_q = sort_queue(entries)
    assert sorted_q[0].job_id == 2  # VIP first
    assert sorted_q[1].job_id == 1


def test_starvation_protection():
    now = time.time()
    entries = [
        # VIP queued just now
        QueueEntry(job_id=1, user_id=10, user_tier="vip", priority=1, queued_at=now),
        # Standard queued very long ago — bonus capped at 2.0, so effective = 3 - 2 = 1.0
        # Need enough wait to push below VIP's 1.0. Use 3x threshold for bonus cap of 2.0
        # effective_priority: VIP=1.0, Standard=3.0-2.0=1.0 (tie, but we need standard lower)
        # Actually max bonus is 2.0, so standard effective = 1.0, same as VIP = 1.0
        # Increase max bonus or test with power_user (priority=2) instead
        QueueEntry(
            job_id=2,
            user_id=20,
            user_tier="power_user",
            priority=2,
            queued_at=now - STARVATION_THRESHOLD_SECONDS * 3,
        ),
    ]
    sorted_q = sort_queue(entries)
    # Power user waited so long (bonus=2.0) that effective=2-2=0, below VIP's 1.0
    assert sorted_q[0].job_id == 2


def test_same_tier_fifo():
    now = time.time()
    entries = [
        QueueEntry(job_id=1, user_id=10, user_tier="standard", priority=3, queued_at=now - 10),
        QueueEntry(job_id=2, user_id=20, user_tier="standard", priority=3, queued_at=now),
    ]
    sorted_q = sort_queue(entries)
    assert sorted_q[0].job_id == 1  # Earlier first


def test_get_queue_position():
    now = time.time()
    entries = [
        QueueEntry(job_id=1, user_id=10, user_tier="standard", priority=3, queued_at=now - 20),
        QueueEntry(job_id=2, user_id=20, user_tier="vip", priority=1, queued_at=now),
        QueueEntry(job_id=3, user_id=30, user_tier="standard", priority=3, queued_at=now - 10),
    ]
    assert get_queue_position(2, entries) == 1  # VIP first
    assert get_queue_position(1, entries) == 2  # Earlier standard
    assert get_queue_position(3, entries) == 3  # Later standard


def test_queue_position_not_found():
    assert get_queue_position(999, []) == -1


def test_admin_highest_priority():
    now = time.time()
    entries = [
        QueueEntry(job_id=1, user_id=10, user_tier="vip", priority=1, queued_at=now),
        QueueEntry(job_id=2, user_id=20, user_tier="admin", priority=0, queued_at=now),
    ]
    sorted_q = sort_queue(entries)
    assert sorted_q[0].job_id == 2  # Admin first
