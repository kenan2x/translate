from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from celery import Celery

from app.config import Settings

logger = logging.getLogger(__name__)

# Redis URL: env'den oku, yoksa localhost fallback
_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("translate")
celery_app.config_from_object(
    {
        "broker_url": _redis_url,
        "result_backend": _redis_url,
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
        secure=settings.MINIO_SECURE,
    )

    channel = f"job:{job_id}"

    def publish_event(event_type: str, data: dict):
        r.publish(channel, json.dumps({"event": event_type, "data": data}))

    try:
        publish_event("job_status", {"job_id": job_id, "status": "processing"})
        pdf_data = storage.download(input_object_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"
            input_path.write_bytes(pdf_data)

            from app.services.pdf_translator import PDFTranslator, PageResult

            translator = PDFTranslator(
                vllm_base_url=settings.VLLM_BASE_URL,
                vllm_model=settings.VLLM_MODEL,
                vllm_api_key=settings.VLLM_API_KEY,
                thread_count=settings.PDF_ENGINE_THREAD_COUNT,
            )

            def page_callback(result: PageResult):
                publish_event(
                    "page_done",
                    {
                        "page": result.page,
                        "total": result.total,
                        "content": result.translated,
                        "elapsed_ms": result.elapsed_ms,
                        "job_id": job_id,
                    },
                )

            results = translator.translate(
                str(input_path), callback=page_callback,
            )

            total_pages = len(results)

            # Cevirilmis metinleri JSON olarak MinIO'ya yukle
            translated_data = json.dumps(
                [{"page": r.page, "content": r.translated} for r in results],
                ensure_ascii=False,
            ).encode("utf-8")
            result_object = storage.upload(
                translated_data, f"{job_id}_translated.json", user_id,
            )

        download_url = f"/api/v1/download/{job_id}"
        publish_event(
            "job_complete",
            {
                "job_id": job_id,
                "download_url": download_url,
                "translated_path": result_object,
                "total_pages": total_pages,
            },
        )

        return {
            "job_id": job_id,
            "translated_path": result_object,
            "total_pages": total_pages,
            "status": "completed",
        }

    except Exception as e:
        logger.exception(f"Translation failed for job {job_id}")
        publish_event(
            "error",
            {"job_id": job_id, "code": "TRANSLATION_FAILED", "message": str(e)},
        )
        return {"job_id": job_id, "status": "failed", "error": str(e)}
