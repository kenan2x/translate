# Faz 1 — Temel Ceviri (MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kullanici PDF yukler, ceviri baslar, sonuc indirilir. Tek kullanici akisi calisan bir MVP.

**Architecture:** FastAPI backend + Celery worker + Next.js frontend. PDF upload -> MinIO storage -> Celery task (PDFMathTranslate via vLLM) -> SSE stream -> download. Auth via Authentik JWT. PostgreSQL metadata, Redis queue/cache.

**Tech Stack:** FastAPI, Celery, Redis, PostgreSQL (SQLAlchemy 2 async), MinIO, PDFMathTranslate, Next.js 14, PDF.js, Vitest, pytest

---

## File Structure

### Backend

```
backend/
├── pyproject.toml                      # Dependencies + project config
├── Dockerfile                          # Backend container
├── alembic.ini                         # Alembic config
├── alembic/
│   ├── env.py                          # Alembic environment
│   └── versions/                       # Migration files
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app factory
│   ├── config.py                       # Pydantic Settings
│   ├── dependencies.py                 # Dependency injection (db, redis, auth)
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py              # v1 router aggregator
│   │       ├── upload.py              # POST /api/v1/upload
│   │       ├── jobs.py                # GET /api/v1/jobs/{id} (SSE)
│   │       └── download.py           # GET /api/v1/download/{id}
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py                    # Authentik JWT verification
│   │   ├── quota.py                   # Quota check/consume
│   │   ├── queue.py                   # Celery app + tasks
│   │   └── sse.py                     # SSE event helpers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_validator.py           # 7-step validation
│   │   ├── pdf_translator.py          # PDFMathTranslate wrapper
│   │   └── storage.py                 # MinIO operations
│   └── models/
│       ├── __init__.py
│       ├── base.py                    # SQLAlchemy Base
│       ├── user.py                    # User model
│       ├── job.py                     # Job model
│       └── quota.py                   # QuotaUsage model
└── tests/
    ├── __init__.py
    ├── conftest.py                    # Shared fixtures
    ├── unit/
    │   ├── __init__.py
    │   ├── test_config.py
    │   ├── test_pdf_validator.py
    │   ├── test_quota.py
    │   ├── test_storage.py
    │   ├── test_sse.py
    │   └── test_auth.py
    └── integration/
        ├── __init__.py
        └── test_upload_flow.py
```

### Frontend

```
frontend/
├── package.json
├── tsconfig.json
├── next.config.ts
├── Dockerfile
├── vitest.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # Main page (upload + split view)
│   │   └── globals.css
│   ├── components/
│   │   ├── UploadZone.tsx
│   │   ├── PDFViewer.tsx
│   │   ├── TranslationPanel.tsx
│   │   └── JobProgress.tsx
│   ├── hooks/
│   │   └── useSSE.ts
│   └── lib/
│       ├── api.ts                     # Backend API client
│       └── auth.ts                    # Authentik session helper
└── __tests__/
    ├── UploadZone.test.tsx
    ├── TranslationPanel.test.tsx
    ├── useSSE.test.ts
    └── api.test.ts
```

### Root

```
translate-test/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/plans/
└── scripts/
    └── seed_glossary.py
```

---

## Task 1: Project Scaffolding & Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `backend/pyproject.toml`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/Dockerfile`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/kenan/translate-test
git init
```

- [ ] **Step 2: Create .gitignore**

Standard Python + Node + Docker ignores.

- [ ] **Step 3: Create .env.example**

All environment variables from CLAUDE.md.

- [ ] **Step 4: Create docker-compose.yml**

Services: postgres, redis, minio with healthchecks.

- [ ] **Step 5: Create backend/pyproject.toml**

FastAPI, SQLAlchemy, Celery, Redis, MinIO, pytest deps.

- [ ] **Step 6: Create frontend scaffolding**

package.json, tsconfig, next.config, vitest.config.

- [ ] **Step 7: Create Dockerfiles**

Backend (Python 3.12) and Frontend (Node 20).

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "chore: project scaffolding with docker-compose, backend, frontend"
```

---

## Task 2: Backend Config & Settings

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/unit/test_config.py`

- [ ] **Step 1: Write failing test for config**

```python
# tests/unit/test_config.py
from app.config import Settings

def test_settings_loads_defaults():
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        REDIS_URL="redis://localhost:6379/0",
        MINIO_ENDPOINT="localhost:9000",
        MINIO_ACCESS_KEY="key",
        MINIO_SECRET_KEY="secret",
        AUTHENTIK_URL="https://auth.example.com",
        AUTHENTIK_CLIENT_ID="cid",
        AUTHENTIK_CLIENT_SECRET="csec",
    )
    assert s.VLLM_BASE_URL == "http://172.30.146.11:8001/v1"
    assert s.VLLM_MODEL == "Qwen/Qwen3.5-122B-A10B-FP8"
    assert s.MINIO_BUCKET == "translate-files"
    assert s.PDF_OUTPUT_TTL_DAYS == 7

def test_settings_requires_database_url():
    import pytest
    with pytest.raises(Exception):
        Settings()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/unit/test_config.py -v
```

- [ ] **Step 3: Implement config.py**

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "translate-files"
    AUTHENTIK_URL: str
    AUTHENTIK_CLIENT_ID: str
    AUTHENTIK_CLIENT_SECRET: str
    VLLM_BASE_URL: str = "http://172.30.146.11:8001/v1"
    VLLM_API_KEY: str = "dummy"
    VLLM_MODEL: str = "Qwen/Qwen3.5-122B-A10B-FP8"
    PDF_ENGINE_THREAD_COUNT: int = 4
    PDF_OUTPUT_TTL_DAYS: int = 7

    model_config = {"env_file": ".env"}
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git add backend/app/ backend/tests/ && git commit -m "feat(config): pydantic settings with all env vars"
```

---

## Task 3: SQLAlchemy Models (User, Job, QuotaUsage)

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/job.py`
- Create: `backend/app/models/quota.py`
- Create: `backend/app/models/__init__.py`
- Test: `backend/tests/unit/test_models.py`

- [ ] **Step 1: Write failing test for models**

```python
# tests/unit/test_models.py
from app.models.user import User, UserTier
from app.models.job import Job, JobStatus
from app.models.quota import QuotaUsage

def test_user_model_has_required_fields():
    u = User(
        external_id="ext-123",
        email="test@takasbank.com.tr",
        display_name="Test User",
        tier=UserTier.STANDARD,
    )
    assert u.tier == UserTier.STANDARD
    assert u.is_active is True

def test_job_model_has_required_fields():
    j = Job(
        user_id=1,
        original_filename="test.pdf",
        original_path="uploads/test.pdf",
        page_count=10,
        status=JobStatus.PENDING,
    )
    assert j.status == JobStatus.PENDING
    assert j.translated_path is None

def test_user_tier_enum():
    assert UserTier.STANDARD == "standard"
    assert UserTier.VIP == "vip"
    assert UserTier.ADMIN == "admin"
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement models**

User model with: id, external_id, email, display_name, department, tier, is_active, created_at, updated_at.
Job model with: id, user_id (FK), original_filename, original_path, translated_path, page_count, translated_pages, status (enum: pending/validating/processing/completed/failed/cancelled), priority, error_message, created_at, started_at, completed_at.
QuotaUsage: id, user_id (FK), date, pages_used, period_type (daily/monthly).

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(models): User, Job, QuotaUsage SQLAlchemy models"
```

---

## Task 4: Alembic Setup & Initial Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/` (auto-generated)

- [ ] **Step 1: Initialize alembic**

```bash
cd backend && alembic init alembic
```

- [ ] **Step 2: Configure alembic env.py for async**
- [ ] **Step 3: Generate initial migration**

```bash
alembic revision --autogenerate -m "initial tables"
```

- [ ] **Step 4: Review generated migration**
- [ ] **Step 5: Commit**

```bash
git commit -m "chore(db): alembic setup with initial migration"
```

---

## Task 5: FastAPI App Factory & Dependencies

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/dependencies.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/router.py`
- Test: `backend/tests/unit/test_main.py`

- [ ] **Step 1: Write failing test for app creation**

```python
# tests/unit/test_main.py
from fastapi.testclient import TestClient
from app.main import create_app

def test_app_has_health_endpoint():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_app_has_v1_routes():
    app = create_app()
    paths = [r.path for r in app.routes]
    assert "/api/v1/upload" in paths or any("/api/v1" in p for p in paths)
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement main.py and dependencies**

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1.router import v1_router

def create_app() -> FastAPI:
    app = FastAPI(title="Takasbank PDF Translator")
    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(app): FastAPI app factory with health endpoint and v1 router"
```

---

## Task 6: Authentik JWT Auth

**Files:**
- Create: `backend/app/core/auth.py`
- Test: `backend/tests/unit/test_auth.py`

- [ ] **Step 1: Write failing test for JWT verification**

```python
# tests/unit/test_auth.py
import pytest
from unittest.mock import patch, AsyncMock
from app.core.auth import verify_token, AuthError

def test_missing_token_raises():
    with pytest.raises(AuthError):
        # sync wrapper for test
        import asyncio
        asyncio.run(verify_token(None))

def test_invalid_token_raises():
    with pytest.raises(AuthError):
        import asyncio
        asyncio.run(verify_token("invalid.jwt.token"))

@patch("app.core.auth.fetch_jwks")
def test_valid_token_returns_user_info(mock_jwks):
    # Mock JWKS and decode flow
    pass
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement auth.py**

JWKS fetch from Authentik, JWT decode with python-jose, extract user info (sub, email, groups).

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(auth): Authentik JWT verification with JWKS"
```

---

## Task 7: PDF Validator (7-Step)

**Files:**
- Create: `backend/app/services/pdf_validator.py`
- Test: `backend/tests/unit/test_pdf_validator.py`

- [ ] **Step 1: Write failing tests for all 7 validation steps**

```python
# tests/unit/test_pdf_validator.py
import pytest
from app.services.pdf_validator import PDFValidator, ValidationResult, ValidationStep

class TestFormatCheck:
    def test_valid_pdf_passes(self, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 ...")
        result = PDFValidator.check_format(pdf)
        assert result.status == "passed"

    def test_non_pdf_fails(self, tmp_path):
        txt = tmp_path / "test.txt"
        txt.write_bytes(b"not a pdf")
        result = PDFValidator.check_format(txt)
        assert result.status == "failed"
        assert result.step == ValidationStep.FORMAT_CHECK

class TestSizeCheck:
    def test_within_limit_passes(self, tmp_path):
        pdf = tmp_path / "small.pdf"
        pdf.write_bytes(b"%PDF-" + b"x" * 1000)
        result = PDFValidator.check_size(pdf, max_mb=50)
        assert result.status == "passed"

    def test_over_limit_fails(self, tmp_path):
        pdf = tmp_path / "big.pdf"
        pdf.write_bytes(b"%PDF-" + b"x" * (51 * 1024 * 1024))
        result = PDFValidator.check_size(pdf, max_mb=50)
        assert result.status == "failed"

class TestEncryptionCheck:
    def test_unencrypted_passes(self, sample_pdf):
        result = PDFValidator.check_encryption(sample_pdf)
        assert result.status == "passed"

    def test_encrypted_fails(self, encrypted_pdf):
        result = PDFValidator.check_encryption(encrypted_pdf)
        assert result.status == "failed"

class TestPageCount:
    def test_within_limit_passes(self, sample_pdf):
        result = PDFValidator.check_page_count(sample_pdf, max_pages=100)
        assert result.status == "passed"
        assert result.details["pages"] > 0

class TestQuotaCheck:
    def test_sufficient_quota_passes(self):
        result = PDFValidator.check_quota(
            pages=10, daily_used=40, daily_limit=50,
            monthly_used=400, monthly_limit=500
        )
        assert result.status == "passed"

    def test_daily_exceeded_fails(self):
        result = PDFValidator.check_quota(
            pages=10, daily_used=45, daily_limit=50,
            monthly_used=0, monthly_limit=500
        )
        assert result.status == "failed"

    def test_monthly_exceeded_fails(self):
        result = PDFValidator.check_quota(
            pages=10, daily_used=0, daily_limit=50,
            monthly_used=495, monthly_limit=500
        )
        assert result.status == "failed"

    def test_unlimited_quota_always_passes(self):
        result = PDFValidator.check_quota(
            pages=999, daily_used=999, daily_limit=None,
            monthly_used=999, monthly_limit=None
        )
        assert result.status == "passed"
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement pdf_validator.py**

ValidationStep enum, ValidationResult dataclass, PDFValidator class with static methods for each step. Uses PyMuPDF for encryption/page count.

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(validator): 7-step PDF validation with tests"
```

---

## Task 8: MinIO Storage Service

**Files:**
- Create: `backend/app/services/storage.py`
- Test: `backend/tests/unit/test_storage.py`

- [ ] **Step 1: Write failing tests for storage operations**

```python
# tests/unit/test_storage.py
import pytest
from unittest.mock import MagicMock, patch
from app.services.storage import StorageService

@patch("app.services.storage.Minio")
def test_upload_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_minio_cls.return_value = mock_client
    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    path = svc.upload(b"content", "test.pdf", "user-123")
    assert "user-123" in path
    assert path.endswith(".pdf")
    mock_client.put_object.assert_called_once()

@patch("app.services.storage.Minio")
def test_download_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.read.return_value = b"pdf-content"
    mock_client.get_object.return_value = mock_response
    mock_minio_cls.return_value = mock_client
    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    data = svc.download("uploads/user-123/test.pdf")
    assert data == b"pdf-content"

@patch("app.services.storage.Minio")
def test_delete_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_minio_cls.return_value = mock_client
    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    svc.delete("uploads/user-123/test.pdf")
    mock_client.remove_object.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement storage.py**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(storage): MinIO storage service with upload/download/delete"
```

---

## Task 9: SSE Event Helpers

**Files:**
- Create: `backend/app/core/sse.py`
- Test: `backend/tests/unit/test_sse.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_sse.py
import json
import pytest
from app.core.sse import format_sse_event, SSEEventType

def test_format_job_status_event():
    result = format_sse_event(
        SSEEventType.JOB_STATUS,
        {"job_id": "abc", "status": "processing", "queue_position": 2}
    )
    assert result.startswith("event: job_status\n")
    assert '"job_id": "abc"' in result
    assert result.endswith("\n\n")

def test_format_page_done_event():
    result = format_sse_event(
        SSEEventType.PAGE_DONE,
        {"page": 3, "content": "translated text", "elapsed_ms": 4200}
    )
    assert "event: page_done" in result

def test_format_validation_event():
    result = format_sse_event(
        SSEEventType.VALIDATION,
        {"step": "QUOTA_CHECK", "status": "passed"}
    )
    assert "event: validation" in result
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement sse.py**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(sse): SSE event formatter with typed events"
```

---

## Task 10: Quota Service

**Files:**
- Create: `backend/app/core/quota.py`
- Test: `backend/tests/unit/test_quota.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_quota.py
import pytest
from app.core.quota import QuotaService, TIER_CONFIG
from app.models.user import UserTier

def test_tier_config_standard():
    cfg = TIER_CONFIG[UserTier.STANDARD]
    assert cfg["daily"] == 50
    assert cfg["monthly"] == 500
    assert cfg["max_file_mb"] == 50
    assert cfg["max_pages"] == 100

def test_tier_config_vip_unlimited():
    cfg = TIER_CONFIG[UserTier.VIP]
    assert cfg["daily"] is None
    assert cfg["monthly"] is None

def test_check_quota_passes_when_enough():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=10,
        daily_used=30,
        monthly_used=400
    )
    assert result.allowed is True

def test_check_quota_fails_daily():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=10,
        daily_used=45,
        monthly_used=0
    )
    assert result.allowed is False
    assert "daily" in result.reason.lower()

def test_check_quota_vip_always_passes():
    result = QuotaService.check(
        tier=UserTier.VIP,
        pages_requested=9999,
        daily_used=9999,
        monthly_used=9999
    )
    assert result.allowed is True
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement quota.py**

TIER_CONFIG dict, QuotaService.check() returns QuotaCheckResult(allowed, reason, details).

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(quota): quota service with tier-based limits"
```

---

## Task 11: Celery App & Translation Task

**Files:**
- Create: `backend/app/core/queue.py`
- Create: `backend/app/services/pdf_translator.py`
- Test: `backend/tests/unit/test_translator.py`

- [ ] **Step 1: Write failing tests for translator**

```python
# tests/unit/test_translator.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_translator import PDFTranslator

@patch("app.services.pdf_translator.translate_pdf")
def test_translate_returns_output_path(mock_translate):
    mock_translate.return_value = "/tmp/output.pdf"
    translator = PDFTranslator(
        vllm_base_url="http://172.30.146.11:8001/v1",
        vllm_model="Qwen/Qwen3.5-122B-A10B-FP8",
    )
    result = translator.translate(
        input_path="/tmp/input.pdf",
        output_dir="/tmp/output",
        callback=None
    )
    assert result.endswith(".pdf")

@patch("app.services.pdf_translator.translate_pdf")
def test_translate_calls_callback_per_page(mock_translate):
    pages_reported = []
    def callback(page, total):
        pages_reported.append(page)

    mock_translate.side_effect = lambda *a, **kw: (
        kw.get("callback") and [kw["callback"](i, 5) for i in range(1, 6)],
        "/tmp/out.pdf"
    )[-1]

    translator = PDFTranslator(
        vllm_base_url="http://172.30.146.11:8001/v1",
        vllm_model="Qwen/Qwen3.5-122B-A10B-FP8",
    )
    translator.translate("/tmp/in.pdf", "/tmp/out", callback=callback)
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement pdf_translator.py and queue.py**

PDFTranslator wraps PDFMathTranslate Python API. Celery app with translate_pdf_task that: downloads from MinIO, runs translator, uploads result, publishes SSE events via Redis.

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(worker): Celery task + PDFMathTranslate translator wrapper"
```

---

## Task 12: Upload Endpoint

**Files:**
- Create: `backend/app/api/v1/upload.py`
- Test: `backend/tests/integration/test_upload_flow.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/integration/test_upload_flow.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

@patch("app.api.v1.upload.verify_token")
@patch("app.api.v1.upload.get_storage")
@patch("app.api.v1.upload.translate_pdf_task")
def test_upload_valid_pdf(mock_task, mock_storage, mock_auth, client, auth_headers, tmp_path):
    mock_auth.return_value = {"sub": "user-1", "email": "test@test.com", "tier": "standard"}
    mock_storage.return_value.upload.return_value = "uploads/user-1/test.pdf"
    mock_task.delay.return_value = MagicMock(id="task-123")

    pdf_content = b"%PDF-1.4 test content"
    resp = client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data

@patch("app.api.v1.upload.verify_token")
def test_upload_non_pdf_rejected(mock_auth, client, auth_headers):
    mock_auth.return_value = {"sub": "user-1", "email": "test@test.com", "tier": "standard"}
    resp = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 422

def test_upload_without_auth_rejected(client):
    resp = client.post("/api/v1/upload", files={"file": ("t.pdf", b"%PDF-", "application/pdf")})
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement upload.py**

Endpoint receives file, runs validation pipeline, saves to MinIO, creates Job record, dispatches Celery task, returns job_id.

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(upload): PDF upload endpoint with validation pipeline"
```

---

## Task 13: SSE Stream Endpoint (Jobs)

**Files:**
- Create: `backend/app/api/v1/jobs.py`
- Test: `backend/tests/unit/test_sse_endpoint.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_sse_endpoint.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import create_app

@pytest.fixture
def client():
    return TestClient(create_app())

@patch("app.api.v1.jobs.verify_token")
@patch("app.api.v1.jobs.get_redis")
def test_sse_stream_returns_events(mock_redis, mock_auth, client):
    mock_auth.return_value = {"sub": "user-1"}
    # Mock Redis pubsub
    mock_pubsub = MagicMock()
    mock_pubsub.listen.return_value = [
        {"type": "message", "data": b'{"event":"page_done","data":{"page":1}}'}
    ]
    mock_redis.return_value.pubsub.return_value = mock_pubsub

    resp = client.get(
        "/api/v1/jobs/job-123",
        headers={"Authorization": "Bearer token"}
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement jobs.py**

SSE endpoint that subscribes to Redis channel for job events, streams to client.

- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(jobs): SSE stream endpoint for job progress"
```

---

## Task 14: Download Endpoint

**Files:**
- Create: `backend/app/api/v1/download.py`
- Test: `backend/tests/unit/test_download.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_download.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import create_app

@pytest.fixture
def client():
    return TestClient(create_app())

@patch("app.api.v1.download.verify_token")
@patch("app.api.v1.download.get_db")
@patch("app.api.v1.download.get_storage")
def test_download_completed_job(mock_storage, mock_db, mock_auth, client):
    mock_auth.return_value = {"sub": "user-1"}
    # Mock DB returns completed job owned by user
    mock_job = MagicMock(
        user_id="user-1", status="completed",
        translated_path="output/result.pdf",
        original_filename="original.pdf"
    )
    mock_db.return_value.get.return_value = mock_job
    mock_storage.return_value.download.return_value = b"%PDF-1.4 translated"

    resp = client.get(
        "/api/v1/download/job-123",
        headers={"Authorization": "Bearer token"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"

@patch("app.api.v1.download.verify_token")
@patch("app.api.v1.download.get_db")
def test_download_other_users_job_denied(mock_db, mock_auth, client):
    mock_auth.return_value = {"sub": "user-2"}
    mock_job = MagicMock(user_id="user-1", status="completed")
    mock_db.return_value.get.return_value = mock_job

    resp = client.get(
        "/api/v1/download/job-123",
        headers={"Authorization": "Bearer token"}
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement download.py**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(download): translated PDF download endpoint with auth check"
```

---

## Task 15: Frontend — Upload Zone Component

**Files:**
- Create: `frontend/src/components/UploadZone.tsx`
- Create: `frontend/src/lib/api.ts`
- Test: `frontend/__tests__/UploadZone.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// __tests__/UploadZone.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { UploadZone } from '@/components/UploadZone'

test('renders upload area with drag and drop', () => {
  render(<UploadZone onUpload={vi.fn()} />)
  expect(screen.getByText(/PDF/i)).toBeInTheDocument()
})

test('calls onUpload when valid file selected', async () => {
  const onUpload = vi.fn()
  render(<UploadZone onUpload={onUpload} />)
  const input = screen.getByTestId('file-input')
  const file = new File(['%PDF-test'], 'test.pdf', { type: 'application/pdf' })
  fireEvent.change(input, { target: { files: [file] } })
  expect(onUpload).toHaveBeenCalledWith(file)
})

test('rejects non-PDF files', async () => {
  const onUpload = vi.fn()
  render(<UploadZone onUpload={onUpload} />)
  const input = screen.getByTestId('file-input')
  const file = new File(['text'], 'test.txt', { type: 'text/plain' })
  fireEvent.change(input, { target: { files: [file] } })
  expect(onUpload).not.toHaveBeenCalled()
  expect(screen.getByText(/PDF/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement UploadZone.tsx and api.ts**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(frontend): UploadZone component with drag-and-drop"
```

---

## Task 16: Frontend — SSE Hook & Translation Panel

**Files:**
- Create: `frontend/src/hooks/useSSE.ts`
- Create: `frontend/src/components/TranslationPanel.tsx`
- Create: `frontend/src/components/JobProgress.tsx`
- Test: `frontend/__tests__/useSSE.test.ts`
- Test: `frontend/__tests__/TranslationPanel.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
// __tests__/useSSE.test.ts
import { renderHook, act } from '@testing-library/react'
import { useSSE } from '@/hooks/useSSE'

test('connects to SSE endpoint and receives events', () => {
  // Mock EventSource
  const mockES = { addEventListener: vi.fn(), close: vi.fn() }
  vi.stubGlobal('EventSource', vi.fn(() => mockES))

  const { result } = renderHook(() => useSSE('job-123'))
  expect(EventSource).toHaveBeenCalledWith(expect.stringContaining('job-123'))
})

// __tests__/TranslationPanel.test.tsx
import { render, screen } from '@testing-library/react'
import { TranslationPanel } from '@/components/TranslationPanel'

test('shows translated pages as they arrive', () => {
  render(<TranslationPanel pages={[
    { page: 1, content: 'Translated page 1' }
  ]} currentPage={1} />)
  expect(screen.getByText('Translated page 1')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement useSSE, TranslationPanel, JobProgress**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(frontend): SSE hook, TranslationPanel, JobProgress components"
```

---

## Task 17: Frontend — PDF Viewer & Main Page

**Files:**
- Create: `frontend/src/components/PDFViewer.tsx`
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/lib/auth.ts`

- [ ] **Step 1: Write failing test**

```tsx
// __tests__/PDFViewer.test.tsx
import { render, screen } from '@testing-library/react'
import { PDFViewer } from '@/components/PDFViewer'

test('renders PDF viewer container', () => {
  render(<PDFViewer url="/test.pdf" currentPage={1} onPageChange={vi.fn()} />)
  expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement PDFViewer and wire up main page**

Split view: left PDF.js viewer, right TranslationPanel. Upload → job creation → SSE stream → page-by-page display.

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(frontend): PDF viewer, split view main page"
```

---

## Task 18: Integration & Docker Compose Verification

- [ ] **Step 1: Verify docker-compose services start**

```bash
docker compose up -d postgres redis minio
docker compose ps
```

- [ ] **Step 2: Run backend tests**

```bash
cd backend && pytest tests/ -v --tb=short
```

- [ ] **Step 3: Run frontend tests**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 4: Manual smoke test**

Start backend + frontend dev servers, verify upload → process → download flow works.

- [ ] **Step 5: Final commit**

```bash
git commit -m "chore: Faz 1 MVP complete — upload, translate, download flow"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Project scaffolding | - |
| 2 | Config/Settings | 2 |
| 3 | DB Models | 3 |
| 4 | Alembic migration | - |
| 5 | FastAPI app factory | 2 |
| 6 | Authentik auth | 3 |
| 7 | PDF Validator (7-step) | 10+ |
| 8 | MinIO storage | 3 |
| 9 | SSE helpers | 3 |
| 10 | Quota service | 5 |
| 11 | Celery + translator | 2 |
| 12 | Upload endpoint | 3 |
| 13 | SSE stream endpoint | 1 |
| 14 | Download endpoint | 2 |
| 15 | Frontend: UploadZone | 3 |
| 16 | Frontend: SSE + TranslationPanel | 3 |
| 17 | Frontend: PDFViewer + main page | 1 |
| 18 | Integration verification | - |

**Total: 18 tasks, ~44 tests**
