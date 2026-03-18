from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.auth import get_current_user
from app.core.sse import SSEEventType, format_sse_event, format_sse_keepalive

router = APIRouter()


@router.get("/jobs/{job_id}")
async def stream_job_progress(
    job_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """SSE stream for job progress."""
    import redis.asyncio as aioredis

    from app.dependencies import get_settings

    settings = get_settings()

    async def event_generator():
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        channel = f"job:{job_id}"
        await pubsub.subscribe(channel)

        try:
            # Send initial connection event
            yield format_sse_event(
                SSEEventType.JOB_STATUS,
                {"job_id": job_id, "status": "connected"},
            )

            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    event_type = data.get("event", "job_status")
                    yield f"event: {event_type}\ndata: {json.dumps(data.get('data', data))}\n\n"

                    # End stream on completion or error
                    if event_type in ("job_complete", "error"):
                        break
                else:
                    # Keepalive
                    yield format_sse_keepalive()
                    await asyncio.sleep(1)
        finally:
            await pubsub.unsubscribe(channel)
            await r.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Cancel a running job."""
    from app.core.queue import celery_app

    celery_app.control.revoke(job_id, terminate=True)
    return {"job_id": job_id, "status": "cancelled"}
