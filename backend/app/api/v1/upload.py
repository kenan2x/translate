from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.core.auth import get_current_user
from app.core.quota import QuotaService, TIER_CONFIG
from app.core.rate_limit import RateLimiter, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW
from app.models.user import UserTier
from app.services.pdf_validator import PDFValidator

router = APIRouter()


def _check_rate_limit(user_id: str) -> None:
    """Check upload rate limit. Raises HTTPException(429) if exceeded. Fail-open on Redis errors."""
    try:
        import redis
        from app.dependencies import get_settings

        settings = get_settings()
        r = redis.from_url(settings.REDIS_URL)
        limiter = RateLimiter(r)
        rate_key = f"rate:upload:{user_id}"
        if not limiter.check(rate_key, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW):
            remaining = limiter.get_remaining(rate_key, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {UPLOAD_RATE_LIMIT} uploads per {UPLOAD_RATE_WINDOW}s. Remaining: {remaining}",
            )
    except HTTPException:
        raise
    except Exception:
        pass  # If Redis unavailable, allow upload (fail-open)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Upload a PDF for translation."""
    user_id = current_user.get("sub", "anonymous")

    # Rate limit check
    _check_rate_limit(user_id)

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty file")

    # Check format (magic bytes)
    if not content[:5] == b"%PDF-":
        raise HTTPException(status_code=422, detail="File is not a valid PDF")

    # Write to temp file for validation
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        user_tier = UserTier(current_user.get("tier", "standard"))
        tier_cfg = TIER_CONFIG[user_tier.value]

        # Size check
        size_result = PDFValidator.check_size(tmp_path, tier_cfg["max_file_mb"])
        if size_result.status == "failed":
            raise HTTPException(status_code=422, detail=size_result.message)

        from app.services.storage import StorageService
        from app.dependencies import get_settings

        settings = get_settings()
        storage = StorageService(
            settings.MINIO_ENDPOINT,
            settings.MINIO_ACCESS_KEY,
            settings.MINIO_SECRET_KEY,
            settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
        )

        object_path = storage.upload(content, file.filename or "upload.pdf", user_id)

        from app.core.queue import translate_pdf_task

        task = translate_pdf_task.delay(
            job_id=0,
            input_object_path=object_path,
            user_id=user_id,
        )

        return {
            "job_id": task.id,
            "status": "pending",
            "filename": file.filename,
            "message": "PDF uploaded, translation queued",
        }
    finally:
        tmp_path.unlink(missing_ok=True)
