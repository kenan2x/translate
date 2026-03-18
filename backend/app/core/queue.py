from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from celery import Celery

from app.config import Settings

logger = logging.getLogger(__name__)

# Celery app - configured at import time with defaults
# Actual settings are loaded from env
celery_app = Celery("translate")
celery_app.config_from_object(
    {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "Europe/Istanbul",
        "task_track_started": True,
        # Priority queue: 0 (highest) to 9 (lowest)
        "broker_transport_options": {
            "priority_steps": list(range(10)),
            "sep": ":",
            "queue_order_strategy": "priority",
        },
        "task_default_priority": 5,
    }
)


def configure_celery(settings: Settings) -> None:
    celery_app.conf.update(
        broker_url=settings.REDIS_URL,
        result_backend=settings.REDIS_URL,
    )


@celery_app.task(bind=True, name="translate_pdf")
def translate_pdf_task(self, job_id: int, input_object_path: str, user_id: str):
    """Celery task: download PDF from MinIO, translate, upload result."""
    import redis as redis_lib

    settings = Settings()
    r = redis_lib.Redis.from_url(settings.REDIS_URL)

    from app.services.storage import StorageService

    storage = StorageService(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET,
    )

    channel = f"job:{job_id}"

    def publish_event(event_type: str, data: dict):
        r.publish(channel, json.dumps({"event": event_type, "data": data}))

    try:
        # Download input PDF
        publish_event("job_status", {"job_id": job_id, "status": "processing"})
        pdf_data = storage.download(input_object_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"
            output_dir = Path(tmpdir) / "output"
            input_path.write_bytes(pdf_data)

            from app.services.pdf_translator import PDFTranslator

            translator = PDFTranslator(
                vllm_base_url=settings.VLLM_BASE_URL,
                vllm_model=settings.VLLM_MODEL,
                vllm_api_key=settings.VLLM_API_KEY,
                thread_count=settings.PDF_ENGINE_THREAD_COUNT,
            )

            def page_callback(current_page: int, total_pages: int):
                publish_event(
                    "page_done",
                    {"page": current_page, "total": total_pages, "job_id": job_id},
                )

            output_path = translator.translate(
                str(input_path), str(output_dir), callback=page_callback
            )

            # Upload result to MinIO
            result_data = Path(output_path).read_bytes()
            result_object = storage.upload(result_data, "translated.pdf", user_id)

        publish_event(
            "job_complete",
            {"job_id": job_id, "translated_path": result_object},
        )

        return {"job_id": job_id, "translated_path": result_object, "status": "completed"}

    except Exception as e:
        logger.exception(f"Translation failed for job {job_id}")
        publish_event("error", {"job_id": job_id, "code": "TRANSLATION_FAILED", "message": str(e)})
        return {"job_id": job_id, "status": "failed", "error": str(e)}
