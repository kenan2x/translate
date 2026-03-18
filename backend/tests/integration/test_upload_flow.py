import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app
from app.core.auth import get_current_user


def _make_app_with_mock_auth(user_data):
    """Create app with auth dependency overridden."""
    app = create_app()

    async def mock_auth():
        return user_data

    app.dependency_overrides[get_current_user] = mock_auth
    return app


def test_upload_valid_pdf():
    app = _make_app_with_mock_auth(
        {"sub": "user-1", "email": "test@test.com", "name": "Test", "groups": [], "tier": "standard"}
    )
    client = TestClient(app)

    with patch("app.api.v1.upload._check_rate_limit"), \
         patch("app.dependencies.get_settings") as mock_settings, \
         patch("app.services.storage.Minio") as mock_minio_cls, \
         patch("app.core.queue.translate_pdf_task") as mock_task:

        mock_s = MagicMock()
        mock_s.MINIO_ENDPOINT = "localhost:9000"
        mock_s.MINIO_ACCESS_KEY = "key"
        mock_s.MINIO_SECRET_KEY = "secret"
        mock_s.MINIO_BUCKET = "bucket"
        mock_settings.return_value = mock_s

        mock_minio_inst = MagicMock()
        mock_minio_inst.bucket_exists.return_value = True
        mock_minio_cls.return_value = mock_minio_inst

        mock_task_result = MagicMock()
        mock_task_result.id = "task-123"
        mock_task.delay.return_value = mock_task_result

        pdf_content = b"%PDF-1.4 test content here"
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"


def test_upload_non_pdf_rejected():
    app = _make_app_with_mock_auth(
        {"sub": "user-1", "email": "test@test.com", "name": "Test", "groups": [], "tier": "standard"}
    )
    client = TestClient(app)

    with patch("app.api.v1.upload._check_rate_limit"):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", b"not a pdf file", "text/plain")},
        )
        assert resp.status_code == 422


def test_upload_empty_file_rejected():
    app = _make_app_with_mock_auth(
        {"sub": "user-1", "email": "test@test.com", "name": "Test", "groups": [], "tier": "standard"}
    )
    client = TestClient(app)

    with patch("app.api.v1.upload._check_rate_limit"):
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 422


def test_upload_without_auth_rejected():
    app = create_app()

    # Override settings to ensure AUTH_DISABLED=False
    from app.dependencies import get_settings
    from app.config import Settings

    def mock_settings():
        return Settings(
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test_db",
            REDIS_URL="redis://localhost:6379/1",
            MINIO_ENDPOINT="localhost:9000",
            MINIO_ACCESS_KEY="testkey",
            MINIO_SECRET_KEY="testsecret",
            AUTH_DISABLED=False,
        )

    app.dependency_overrides[get_settings] = mock_settings
    client = TestClient(app)
    resp = client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert resp.status_code in (401, 403)
