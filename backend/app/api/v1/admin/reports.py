from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/reports", tags=["admin"])


@router.get("/usage")
async def usage_report(
    period: str = "daily",
    group_by: str = "user",
    admin: Dict = Depends(require_admin),
):
    """Get usage report (pages translated) by user or department."""
    # TODO: DB aggregation query
    return {
        "period": period,
        "group_by": group_by,
        "data": [],
    }


@router.get("/top-users")
async def top_users(
    limit: int = 10,
    admin: Dict = Depends(require_admin),
):
    """Get top N users by page count."""
    # TODO: DB aggregation query
    return {"top_users": [], "limit": limit}


@router.get("/export/csv")
async def export_csv(
    period: str = "monthly",
    admin: Dict = Depends(require_admin),
):
    """Export usage report as CSV."""
    csv_content = "user_id,email,pages_translated,period\n"
    # TODO: Generate from DB
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{period}.csv"},
    )
