from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.models.user import UserTier

TIER_CONFIG: Dict[str, Dict] = {
    "standard": {
        "daily": 50,
        "monthly": 500,
        "max_file_mb": 50,
        "max_pages": 100,
        "concurrent": 2,
        "priority": 3,
    },
    "power_user": {
        "daily": 200,
        "monthly": 2000,
        "max_file_mb": 200,
        "max_pages": 300,
        "concurrent": 4,
        "priority": 2,
    },
    "vip": {
        "daily": None,
        "monthly": None,
        "max_file_mb": 500,
        "max_pages": None,
        "concurrent": 10,
        "priority": 1,
    },
    "admin": {
        "daily": None,
        "monthly": None,
        "max_file_mb": None,
        "max_pages": None,
        "concurrent": None,
        "priority": 0,
    },
}


@dataclass
class QuotaCheckResult:
    allowed: bool
    reason: str = ""
    details: Optional[Dict] = None


class QuotaService:
    @staticmethod
    def get_tier_config(tier: UserTier) -> Dict:
        return TIER_CONFIG[tier.value]

    @staticmethod
    def check(
        tier: UserTier,
        pages_requested: int,
        daily_used: int,
        monthly_used: int,
    ) -> QuotaCheckResult:
        cfg = TIER_CONFIG[tier.value]

        daily_limit = cfg["daily"]
        monthly_limit = cfg["monthly"]

        # Unlimited tiers always pass
        if daily_limit is None and monthly_limit is None:
            return QuotaCheckResult(allowed=True)

        # Check daily limit
        if daily_limit is not None and (daily_used + pages_requested) > daily_limit:
            return QuotaCheckResult(
                allowed=False,
                reason=f"Daily quota exceeded ({daily_used}/{daily_limit} used, requesting {pages_requested})",
                details={
                    "daily_used": daily_used,
                    "daily_limit": daily_limit,
                    "pages_requested": pages_requested,
                },
            )

        # Check monthly limit
        if monthly_limit is not None and (monthly_used + pages_requested) > monthly_limit:
            return QuotaCheckResult(
                allowed=False,
                reason=f"Monthly quota exceeded ({monthly_used}/{monthly_limit} used, requesting {pages_requested})",
                details={
                    "monthly_used": monthly_used,
                    "monthly_limit": monthly_limit,
                    "pages_requested": pages_requested,
                },
            )

        return QuotaCheckResult(allowed=True)
