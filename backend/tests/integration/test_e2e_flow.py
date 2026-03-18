"""E2E tests for the full upload -> translate -> download flow."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app
from app.core.auth import get_current_user


def _make_app_with_mock_auth(user_data):
    app = create_app()

    async def mock_auth():
        return user_data

    app.dependency_overrides[get_current_user] = mock_auth
    return app


STANDARD_USER = {
    "sub": "user-e2e",
    "email": "e2e@test.com",
    "name": "E2E Test",
    "groups": [],
    "tier": "standard",
}


def _mock_settings():
    mock_s = MagicMock()
    mock_s.MINIO_ENDPOINT = "localhost:9000"
    mock_s.MINIO_ACCESS_KEY = "key"
    mock_s.MINIO_SECRET_KEY = "secret"
    mock_s.MINIO_BUCKET = "bucket"
    mock_s.REDIS_URL = "redis://localhost:6379/0"
    return mock_s


class TestUploadToDownloadFlow:
    """Test the full lifecycle: upload -> queue -> download."""

    def test_upload_creates_job(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        with patch("app.api.v1.upload._check_rate_limit"), \
             patch("app.dependencies.get_settings") as mock_settings, \
             patch("app.services.storage.Minio") as mock_minio_cls, \
             patch("app.core.queue.translate_pdf_task") as mock_task:

            mock_settings.return_value = _mock_settings()
            mock_minio_inst = MagicMock()
            mock_minio_inst.bucket_exists.return_value = True
            mock_minio_cls.return_value = mock_minio_inst

            mock_task_result = MagicMock()
            mock_task_result.id = "job-e2e-1"
            mock_task.delay.return_value = mock_task_result

            resp = client.post(
                "/api/v1/upload",
                files={"file": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
            )
            assert resp.status_code == 202
            data = resp.json()
            assert data["job_id"] == "job-e2e-1"
            assert data["status"] == "pending"

    def test_download_completed_job(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        with patch("app.core.queue.celery_app") as mock_celery, \
             patch("app.dependencies.get_settings") as mock_settings, \
             patch("app.services.storage.Minio") as mock_minio_cls:

            mock_settings.return_value = _mock_settings()

            mock_minio_inst = MagicMock()
            mock_minio_inst.bucket_exists.return_value = True
            mock_response = MagicMock()
            mock_response.read.return_value = b"%PDF-1.4 translated"
            mock_minio_inst.get_object.return_value = mock_response
            mock_minio_cls.return_value = mock_minio_inst

            mock_result = MagicMock()
            mock_result.ready.return_value = True
            mock_result.result = {
                "status": "completed",
                "translated_path": "outputs/user-e2e/translated.pdf",
            }
            mock_celery.AsyncResult.return_value = mock_result

            resp = client.get("/api/v1/download/job-123")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/pdf"

    def test_download_other_users_file_denied(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        with patch("app.core.queue.celery_app") as mock_celery, \
             patch("app.dependencies.get_settings") as mock_settings, \
             patch("app.services.storage.Minio") as mock_minio_cls:

            mock_settings.return_value = _mock_settings()
            mock_minio_inst = MagicMock()
            mock_minio_inst.bucket_exists.return_value = True
            mock_minio_cls.return_value = mock_minio_inst

            mock_result = MagicMock()
            mock_result.ready.return_value = True
            mock_result.result = {
                "status": "completed",
                "translated_path": "outputs/other-user/translated.pdf",  # Different user!
            }
            mock_celery.AsyncResult.return_value = mock_result

            resp = client.get("/api/v1/download/job-456")
            assert resp.status_code == 403
            assert "Access denied" in resp.json()["detail"]

    def test_download_incomplete_job_404(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        with patch("app.core.queue.celery_app") as mock_celery:
            mock_result = MagicMock()
            mock_result.ready.return_value = False
            mock_celery.AsyncResult.return_value = mock_result

            resp = client.get("/api/v1/download/job-pending")
            assert resp.status_code == 404


class TestRateLimiting:
    """Test rate limiting on upload endpoint."""

    def test_rate_limited_upload_returns_429(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        # Mock _check_rate_limit to raise 429
        with patch(
            "app.api.v1.upload._check_rate_limit",
            side_effect=HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 uploads per 60s. Remaining: 0"),
        ):
            resp = client.post(
                "/api/v1/upload",
                files={"file": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
            )
            assert resp.status_code == 429
            assert "Rate limit" in resp.json()["detail"]


class TestJobSSE:
    """Test SSE stream endpoint."""

    def test_job_cancel(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        with patch("app.core.queue.celery_app") as mock_celery:
            resp = client.delete("/api/v1/jobs/job-cancel-1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "cancelled"
            mock_celery.control.revoke.assert_called_once_with(
                "job-cancel-1", terminate=True
            )


class TestHistory:
    """Test history endpoint."""

    def test_get_history(self):
        app = _make_app_with_mock_auth(STANDARD_USER)
        client = TestClient(app)

        resp = client.get("/api/v1/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
