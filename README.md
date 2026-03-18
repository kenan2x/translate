# Takasbank PDF Ceviri Portali

On-premise PDF ceviri portali. Kullanicilar PDF yukler, sistem sayfa sayfa Turkceye cevirir. Tum LLM ciktilari dahili vLLM sunucusundan gelir — hicbir veri disari cikmaz.

## Mimari

```
Tarayici (PDF.js + SSE)
        |
    Traefik + Authentik SSO
        |
   FastAPI Backend (:8080)
    /  |  \
Redis  PG  MinIO
   |
Celery Worker
   |
PDFMathTranslate + vLLM (Qwen3.5-122B)
```

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI, Celery, SQLAlchemy 2 (async) |
| DB | PostgreSQL 16, Redis 7 |
| Dosya Depolama | MinIO |
| Auth | Authentik SSO (OIDC/JWT) |
| PDF Engine | PDFMathTranslate (pdf2zh) |
| LLM | vLLM — Qwen/Qwen3.5-122B-A10B-FP8 |
| Frontend | Next.js 14, React 18, PDF.js 4 |
| Test | pytest (backend), Vitest (frontend) |

## Hizli Baslangic

### 1. Klonla

```bash
git clone https://github.com/kenan2x/translate.git
cd translate
```

### 2. Env dosyasini hazirla

```bash
cp .env.example .env
```

`.env` icinde doldurilmasi gereken degerler:

```bash
DATABASE_URL=postgresql+asyncpg://translate:translate@postgres:5432/translate_db
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=translate-files
AUTHENTIK_URL=https://auth.takasdom.takasbank.com.tr
AUTHENTIK_CLIENT_ID=<client-id>
AUTHENTIK_CLIENT_SECRET=<client-secret>
```

### 3. Servisleri baslat

```bash
docker compose up -d
```

Bu komut sirasiyla baslatir:
- PostgreSQL 16 + Redis 7 + MinIO (healthcheck ile)
- Backend (Alembic migration + uvicorn)
- Celery Worker (4 concurrent)
- Frontend (Next.js standalone)

### 4. Kontrol

```bash
# Servis durumlari
docker compose ps

# Backend health
curl http://localhost:8080/health

# Frontend
open http://localhost:3000
```

## Erisim Adresleri

| Servis | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| API Docs (Swagger) | http://localhost:8080/docs |
| MinIO Console | http://localhost:9001 |

## Docker Image'lari

Hazir image'lar Docker Hub'da (`linux/amd64`):

```bash
docker pull kenankarakoc/translate-backend:latest
docker pull kenankarakoc/translate-frontend:latest
docker pull kenankarakoc/translate-test-runner:latest
```

## Testler

### Backend testleri (121 test)

```bash
# Docker ile (onerilen)
docker run --rm kenankarakoc/translate-test-runner:latest

# veya lokal
cd backend && pip install -e ".[dev]" && pytest tests/ -v
```

### Frontend testleri (15 test)

```bash
cd frontend && npm ci && npx vitest run
```

### Tum testler birlikte

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Proje Yapisi

```
translate/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # Pydantic settings
│   │   ├── dependencies.py      # DI (auth, db, redis)
│   │   ├── api/v1/              # REST endpoints
│   │   │   ├── upload.py        # PDF upload + validation
│   │   │   ├── jobs.py          # SSE stream + cancel
│   │   │   ├── download.py      # Translated PDF download
│   │   │   ├── history.py       # User history
│   │   │   └── admin/           # 8 admin endpoints
│   │   ├── core/                # Business logic
│   │   │   ├── auth.py          # Authentik JWT
│   │   │   ├── quota.py         # Tier-based quotas
│   │   │   ├── priority.py      # VIP queue + starvation protection
│   │   │   ├── rate_limit.py    # Redis sliding window
│   │   │   ├── queue.py         # Celery tasks
│   │   │   └── sse.py           # SSE event formatting
│   │   ├── services/            # External integrations
│   │   │   ├── pdf_validator.py # 7-step validation
│   │   │   ├── pdf_translator.py# PDFMathTranslate wrapper
│   │   │   ├── storage.py       # MinIO + user isolation
│   │   │   ├── glossary.py      # Technical term management
│   │   │   └── notification.py  # Web Push
│   │   └── models/              # SQLAlchemy models
│   ├── tests/                   # 121 tests (unit + integration + load)
│   ├── alembic/                 # DB migrations
│   ├── Dockerfile               # Production (multi-stage)
│   └── Dockerfile.test          # Test runner
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages (/, /admin, /history)
│   │   ├── components/          # React components
│   │   ├── hooks/               # useSSE, etc.
│   │   └── lib/                 # API client, auth
│   ├── __tests__/               # 15 tests
│   └── Dockerfile               # Production (standalone)
├── scripts/
│   ├── seed_glossary.py         # Initial glossary terms
│   └── create_admin.py          # First admin user
├── docker-compose.yml           # Production stack
├── docker-compose.test.yml      # Test runner stack
└── .env.example                 # Environment template
```

## Kullanici Tipleri

| Tier | Gunluk | Aylik | Max MB | Max Sayfa | Oncelik |
|------|--------|-------|--------|-----------|---------|
| standard | 50 | 500 | 50 | 100 | 3 |
| power_user | 200 | 2000 | 200 | 300 | 2 |
| vip | Sinirsiz | Sinirsiz | 500 | Sinirsiz | 1 |
| admin | Sinirsiz | Sinirsiz | Sinirsiz | Sinirsiz | 0 |

## Admin Panel

`/admin` sayfasindan erisilebilir:

- **Dashboard** — Aktif isler, kuyruk, GPU metrikleri
- **Kullanicilar** — Tier degistirme, gecici VIP, engelleme
- **Kapasite** — Model VRAM/KV-cache hesaplayici
- **Raporlar** — Kullanim raporlari, CSV export
- **Audit Log** — Tum sistem olaylari (90 gun)
- **Glossary** — Teknik terimler (CSV import/export)
- **Ayarlar** — Kota, worker, TTL, bakim modu

## Durdurma

```bash
# Servisleri durdur
docker compose down

# Servisleri durdur + verileri sil
docker compose down -v
```

## Lisans

Internal use only — Takasbank.
