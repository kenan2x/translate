from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/settings", tags=["admin"])


class SystemSettingsUpdate(BaseModel):
    max_workers: Optional[int] = None
    file_ttl_days: Optional[int] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None


@router.get("")
async def get_settings(admin: Dict = Depends(require_admin)):
    """Get current system settings."""
    # TODO: Load from DB/Redis
    return {
        "max_workers": 4,
        "file_ttl_days": 7,
        "maintenance_mode": False,
        "maintenance_message": "",
        "tier_config": {
            "standard": {"daily": 50, "monthly": 500},
            "power_user": {"daily": 200, "monthly": 2000},
            "vip": {"daily": None, "monthly": None},
            "admin": {"daily": None, "monthly": None},
        },
    }


@router.patch("")
async def update_settings(
    body: SystemSettingsUpdate,
    admin: Dict = Depends(require_admin),
):
    """Update system settings."""
    # TODO: Save to DB/Redis + audit log
    updates = {k: v for k, v in body.dict().items() if v is not None}
    return {"updated": updates}
