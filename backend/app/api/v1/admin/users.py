from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user

router = APIRouter(prefix="/admin/users", tags=["admin"])


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    groups = current_user.get("groups", [])
    tier = current_user.get("tier", "standard")
    if tier != "admin" and "admin" not in groups:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class UpdateTierRequest(BaseModel):
    tier: str


class TempVIPRequest(BaseModel):
    until: str  # ISO datetime


@router.get("")
async def list_users(admin: Dict = Depends(require_admin)):
    """List all users with tier and quota status."""
    # TODO: DB query
    return {"users": [], "total": 0}


@router.patch("/{user_id}/tier")
async def update_user_tier(
    user_id: int,
    body: UpdateTierRequest,
    admin: Dict = Depends(require_admin),
):
    """Change a user's tier."""
    valid_tiers = ["standard", "power_user", "vip", "admin"]
    if body.tier not in valid_tiers:
        raise HTTPException(status_code=422, detail=f"Invalid tier. Must be one of: {valid_tiers}")
    # TODO: DB update + audit log
    return {"user_id": user_id, "tier": body.tier, "updated": True}


@router.post("/{user_id}/temp-vip")
async def grant_temp_vip(
    user_id: int,
    body: TempVIPRequest,
    admin: Dict = Depends(require_admin),
):
    """Grant temporary VIP status until specified date."""
    # TODO: Redis + audit log
    return {"user_id": user_id, "temp_vip_until": body.until}


@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    admin: Dict = Depends(require_admin),
):
    """Block a user from using the system."""
    # TODO: DB update + audit log
    return {"user_id": user_id, "blocked": True}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin: Dict = Depends(require_admin),
):
    """Activate a blocked user."""
    # TODO: DB update + audit log
    return {"user_id": user_id, "active": True}
