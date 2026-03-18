from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/audit", tags=["admin"])


@router.get("")
async def get_audit_log(
    action: str = None,
    user_id: int = None,
    page: int = 1,
    per_page: int = 50,
    admin: Dict = Depends(require_admin),
):
    """Get audit log entries with optional filters."""
    # TODO: DB query with filters, 90 day retention
    return {"entries": [], "total": 0, "page": page, "per_page": per_page}


@router.get("/export/csv")
async def export_audit_csv(
    admin: Dict = Depends(require_admin),
):
    """Export audit log as CSV."""
    csv_content = "timestamp,user_id,action,resource_type,resource_id,details,ip_address\n"
    # TODO: Generate from DB
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
