from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.core.auth import get_current_user

router = APIRouter()


@router.get("/download/{job_id}")
async def download_translated_pdf(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Download the translated PDF for a completed job."""
    from app.core.queue import celery_app

    # Get task result
    result = celery_app.AsyncResult(job_id)
    if not result.ready():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not completed yet",
        )

    task_result = result.result
    if not task_result or task_result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=task_result.get("error", "Translation failed") if task_result else "Translation failed",
        )

    translated_path = task_result.get("translated_path")
    if not translated_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translated file not found",
        )

    from app.dependencies import get_settings
    from app.services.storage import StorageService

    settings = get_settings()
    storage = StorageService(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
    )

    try:
        pdf_data = storage.download(translated_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translated file not found in storage",
        )

    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="translated_{job_id}.pdf"',
        },
    )
