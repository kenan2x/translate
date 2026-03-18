from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/quotas", tags=["admin"])


class QuotaOverrideRequest(BaseModel):
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None


@router.get("/{user_id}")
async def get_user_quota(
    user_id: int,
    admin: Dict = Depends(require_admin),
):
    """Get quota details for a specific user."""
    # TODO: Redis + DB query
    return {
        "user_id": user_id,
        "daily_used": 0,
        "daily_limit": 50,
        "monthly_used": 0,
        "monthly_limit": 500,
        "override": None,
    }


@router.put("/{user_id}/override")
async def set_quota_override(
    user_id: int,
    body: QuotaOverrideRequest,
    admin: Dict = Depends(require_admin),
):
    """Set custom quota limits for a user (override tier defaults)."""
    # TODO: DB update + audit log
    return {
        "user_id": user_id,
        "daily_limit": body.daily_limit,
        "monthly_limit": body.monthly_limit,
        "overridden": True,
    }


@router.delete("/{user_id}/override")
async def remove_quota_override(
    user_id: int,
    admin: Dict = Depends(require_admin),
):
    """Remove custom quota override, revert to tier defaults."""
    # TODO: DB update + audit log
    return {"user_id": user_id, "override_removed": True}
