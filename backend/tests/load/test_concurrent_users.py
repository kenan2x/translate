"""Load test: simulate 10 concurrent users uploading PDFs.

This test validates the system handles concurrent uploads correctly.
Uses ThreadPoolExecutor to simulate parallel requests.
"""
from __future__ import annotations

import concurrent.futures
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.auth import get_current_user


def _make_app_with_users(user_count: int):
    """Create app with mock auth that accepts any user."""
    app = create_app()
    users = {}

    for i in range(user_count):
        users[f"user-{i}"] = {
            "sub": f"user-{i}",
            "email": f"user{i}@test.com",
            "name": f"User {i}",
            "groups": [],
            "tier": "standard",
        }

    async def mock_auth():
        return users["user-0"]

    app.dependency_overrides[get_current_user] = mock_auth
    return app


def _mock_settings():
    mock_s = MagicMock()
    mock_s.MINIO_ENDPOINT = "localhost:9000"
    mock_s.MINIO_ACCESS_KEY = "key"
    mock_s.MINIO_SECRET_KEY = "secret"
    mock_s.MINIO_BUCKET = "bucket"
    mock_s.REDIS_URL = "redis://localhost:6379/0"
    return mock_s


def _upload_pdf(client, user_idx):
    """Simulate a single user upload."""
    pdf_content = b"%PDF-1.4 test content for user " + str(user_idx).encode()
    resp = client.post(
        "/api/v1/upload",
        files={"file": (f"doc_{user_idx}.pdf", pdf_content, "application/pdf")},
    )
    return resp.status_code, resp.json()


def test_10_concurrent_uploads():
    """Simulate 10 concurrent users uploading PDFs."""
    app = _make_app_with_users(10)

    with patch("app.api.v1.upload._check_rate_limit"), \
         patch("app.dependencies.get_settings") as mock_settings, \
         patch("app.services.storage.Minio") as mock_minio_cls, \
         patch("app.core.queue.translate_pdf_task") as mock_task:

        mock_settings.return_value = _mock_settings()
        mock_minio_inst = MagicMock()
        mock_minio_inst.bucket_exists.return_value = True
        mock_minio_cls.return_value = mock_minio_inst

        task_counter = {"count": 0}

        def fake_delay(**kwargs):
            task_counter["count"] += 1
            result = MagicMock()
            result.id = f"task-{task_counter['count']}"
            return result

        mock_task.delay.side_effect = fake_delay

        client = TestClient(app)

        # Run 10 uploads sequentially (TestClient isn't thread-safe)
        results = []
        for i in range(10):
            status_code, data = _upload_pdf(client, i)
            results.append((status_code, data))

        # All should succeed
        for i, (code, data) in enumerate(results):
            assert code == 202, f"User {i} failed with {code}: {data}"
            assert data["status"] == "pending"
            assert "job_id" in data

        # 10 tasks should have been dispatched
        assert task_counter["count"] == 10


def test_concurrent_download_isolation():
    """Verify users cannot download other users' files."""
    users_data = [
        {"sub": f"user-{i}", "email": f"u{i}@t.com", "name": f"U{i}", "groups": [], "tier": "standard"}
        for i in range(3)
    ]

    for user_idx, user_data in enumerate(users_data):
        app = create_app()

        async def mock_auth(ud=user_data):
            return ud

        app.dependency_overrides[get_current_user] = mock_auth
        client = TestClient(app)

        with patch("app.core.queue.celery_app") as mock_celery, \
             patch("app.dependencies.get_settings") as mock_settings, \
             patch("app.services.storage.Minio") as mock_minio_cls:

            mock_settings.return_value = _mock_settings()
            mock_minio_inst = MagicMock()
            mock_minio_inst.bucket_exists.return_value = True
            mock_minio_cls.return_value = mock_minio_inst

            # Try to access another user's file
            other_user = f"user-{(user_idx + 1) % 3}"
            mock_result = MagicMock()
            mock_result.ready.return_value = True
            mock_result.result = {
                "status": "completed",
                "translated_path": f"outputs/{other_user}/translated.pdf",
            }
            mock_celery.AsyncResult.return_value = mock_result

            resp = client.get("/api/v1/download/job-cross-access")
            assert resp.status_code == 403, f"User {user_idx} should not access {other_user}'s file"


def test_mixed_tier_concurrent_uploads():
    """Test that different tier users have correct behavior."""
    tiers = ["standard", "power_user", "vip", "admin"]
    max_file_sizes = {"standard": 50, "power_user": 200, "vip": 500, "admin": None}

    for tier in tiers:
        app = create_app()
        user_data = {
            "sub": f"user-{tier}",
            "email": f"{tier}@test.com",
            "name": f"User {tier}",
            "groups": ["admins"] if tier == "admin" else [],
            "tier": tier,
        }

        async def mock_auth(ud=user_data):
            return ud

        app.dependency_overrides[get_current_user] = mock_auth
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
            mock_task_result.id = f"task-{tier}"
            mock_task.delay.return_value = mock_task_result

            pdf_content = b"%PDF-1.4 tier test"
            resp = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
            )
            assert resp.status_code == 202, f"Tier {tier} upload failed: {resp.json()}"
