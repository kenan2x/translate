from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/jobs", tags=["admin"])


@router.get("")
async def list_all_jobs(
    status: str = "",
    user_id: str = "",
    page: int = 1,
    per_page: int = 50,
    admin: Dict = Depends(require_admin),
):
    """List all jobs across all users."""
    # TODO: DB query with filters
    return {"jobs": [], "total": 0, "page": page, "per_page": per_page}


@router.delete("/{job_id}")
async def cancel_job_admin(
    job_id: str,
    admin: Dict = Depends(require_admin),
):
    """Admin: cancel any job."""
    from app.core.queue import celery_app
    celery_app.control.revoke(job_id, terminate=True)
    # TODO: Update DB + audit log
    return {"job_id": job_id, "cancelled": True}


@router.patch("/{job_id}/priority")
async def change_job_priority(
    job_id: str,
    priority: int,
    admin: Dict = Depends(require_admin),
):
    """Change priority of a queued job."""
    # TODO: Update priority in Redis queue
    return {"job_id": job_id, "priority": priority, "updated": True}
