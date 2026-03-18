from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user

router = APIRouter()


@router.get("/history")
async def get_history(
    page: int = 1,
    per_page: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get translation history for current user.

    In production, this queries the jobs table filtered by user_id.
    Returns paginated list of past jobs with status, filename, page count, dates.
    """
    # TODO: Implement DB query when async session is wired up
    # For now, return structure placeholder
    return {
        "items": [],
        "total": 0,
        "page": page,
        "per_page": per_page,
        "user_id": current_user["sub"],
    }
