from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.models.user import UserTier
from app.core.quota import TIER_CONFIG

# Starvation protection: after this many seconds, standard jobs get priority boost
STARVATION_THRESHOLD_SECONDS = 300  # 5 minutes


@dataclass
class QueueEntry:
    job_id: int
    user_id: int
    user_tier: str
    priority: int
    queued_at: float  # timestamp

    @property
    def effective_priority(self) -> float:
        """Lower is higher priority. VIP = 1, standard = 3.
        Starvation protection: waiting time reduces effective priority."""
        wait_time = time.time() - self.queued_at
        starvation_bonus = min(wait_time / STARVATION_THRESHOLD_SECONDS, 2.0)
        return self.priority - starvation_bonus


def get_priority_for_tier(tier: UserTier) -> int:
    """Get queue priority for a user tier. Lower = higher priority."""
    return TIER_CONFIG[tier.value]["priority"]


def sort_queue(entries: List[QueueEntry]) -> List[QueueEntry]:
    """Sort queue entries by effective priority (lower first)."""
    return sorted(entries, key=lambda e: e.effective_priority)


def get_queue_position(job_id: int, entries: List[QueueEntry]) -> int:
    """Get 1-based position of a job in the sorted queue."""
    sorted_entries = sort_queue(entries)
    for i, entry in enumerate(sorted_entries):
        if entry.job_id == job_id:
            return i + 1
    return -1
