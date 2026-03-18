# CLAUDE.md — Takasbank PDF Çeviri Portalı

> **Claude Code için:** Bu dosyayı her oturumun başında oku. Projeye dair tüm kararlar burada.
> Yeni bir özelliğe başlamadan önce `docs/plans/` klasörünü kontrol et.

---

## Proje Özeti

Takasbank iç kullanıcıları için on-premise, tam özellikli bir PDF çeviri portalı.
Kullanıcılar PDF yükler, sol panelde orijinal — sağ panelde Türkçe çeviri sayfa sayfa akar.
Tüm LLM çıktıları `paipsap01` üzerindeki vLLM'den gelir, hiçbir veri dışarı çıkmaz.

**Temel prensipler:**
- Sıfır cloud bağımlılığı — her şey on-premise
- Enterprise-grade: auth, kota, audit, kuyruk yönetimi
- TDD zorunlu — test yazmadan kod yazılmaz
- Her faz sonunda çalışır, deploy edilebilir bir sistem

---

## Superpower Skills — Her Zaman Aktif

Claude Code bu projeyi geliştirirken aşağıdaki skill'leri kullanacak:

```
# Yeni özelliğe başlarken
@writing-plans      → önce plan yaz, sonra kod

# Plan hazırsa ve implemente edilecekse
@executing-plans    → adım adım, test ile birlikte

# Her implementasyonda — istisnasız
@test-driven-development  → önce test, sonra kod

# Bir şey çalışmıyorsa
@systematic-debugging → önce anla, sonra düzelt

# Tamamlandı demeden önce
@verification-before-completion → kanıtla, iddia etme

# Code review gelirse
@receiving-code-review → körü körüne uygulama, değerlendir
```

**Kural:** Hiçbir production kodu test olmadan yazılmaz.
Testi olmayan kod → sil, baştan başla.

---

## Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                    Kullanıcı Tarayıcısı                     │
│   Sol: PDF.js (orijinal)  │  Sağ: SSE stream (çeviri)      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
           Traefik (reverse proxy)
           Authentik SSO middleware
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (plainode01)                    │
│                                                             │
│  /api/v1/upload         POST  → dosya al, validate, job     │
│  /api/v1/jobs/{id}      GET   → SSE stream (progress)       │
│  /api/v1/jobs/{id}      DELETE → job iptal                  │
│  /api/v1/download/{id}  GET   → çevrilmiş PDF               │
│  /api/v1/history        GET   → kullanıcı geçmişi           │
│  /api/v1/admin/*        GET   → admin panel API'leri        │
└──────────┬──────────────────────────────────────────────────┘
           │
     ┌─────┴──────┐
     │            │
     ▼            ▼
  Redis        PostgreSQL
  (Celery      (metadata,
  queue,        audit log,
  SSE buffer,   kota geçmişi,
  cache)        kullanıcılar)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│              Celery Worker                                   │
│                                                             │
│  1. PDF validate (format, şifre, sayfa, kota)               │
│  2. MinIO'ya kaydet                                         │
│  3. PDFMathTranslate Python API → sayfa sayfa               │
│  4. Her sayfa bitti → Redis'e SSE event                     │
│  5. Çıktı PDF → MinIO'ya yaz                                │
│  6. Job tamamlandı → kullanıcıya bildirim                   │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  PDFMathTranslate Python API                                │
│  DocLayout-YOLO → formül/tablo/layout koruması              │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  vLLM (paipsap01:8001)                                      │
│  Model: Qwen/Qwen3.5-122B-A10B-FP8                         │
│  + Glossary inject (storage/network teknik terimler)        │
│  + Custom system prompt (teknik çeviri talimatları)         │
└─────────────────────────────────────────────────────────────┘

MinIO (dosya depolama, 7 gün TTL)
Victoria Metrics ← vLLM /metrics (gerçek zamanlı GPU metrikleri)
```

---

## Proje Yapısı

```
takasbank-translate/
├── CLAUDE.md                    ← bu dosya
├── docker-compose.yml           ← tüm servisler
├── .env.example                 ← env şablonu
│
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app
│   │   ├── config.py            ← settings (pydantic-settings)
│   │   ├── dependencies.py      ← auth, db, redis inject
│   │   │
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── upload.py    ← dosya yükleme + validate
│   │   │   │   ├── jobs.py      ← SSE stream, iptal
│   │   │   │   ├── download.py  ← çıktı PDF
│   │   │   │   ├── history.py   ← kullanıcı geçmişi
│   │   │   │   └── admin/
│   │   │   │       ├── users.py       ← kullanıcı yönetimi
│   │   │   │       ├── quotas.py      ← kota yönetimi
│   │   │   │       ├── jobs.py        ← tüm joblar
│   │   │   │       ├── capacity.py    ← model kapasite hesap
│   │   │   │       ├── reports.py     ← kullanım raporları
│   │   │   │       ├── audit.py       ← audit log
│   │   │   │       ├── glossary.py    ← terim yönetimi
│   │   │   │       └── settings.py    ← sistem ayarları
│   │   │
│   │   ├── core/
│   │   │   ├── auth.py          ← Authentik JWT doğrulama
│   │   │   ├── quota.py         ← kota kontrol/tüketim
│   │   │   ├── queue.py         ← Celery task'lar
│   │   │   ├── sse.py           ← SSE event yönetimi
│   │   │   └── capacity.py      ← model kapasite hesaplama
│   │   │
│   │   ├── services/
│   │   │   ├── pdf_validator.py ← 7 adım doğrulama
│   │   │   ├── pdf_translator.py← PDFMathTranslate wrapper
│   │   │   ├── storage.py       ← MinIO operasyonları
│   │   │   ├── glossary.py      ← terim yükleme/inject
│   │   │   └── notification.py  ← Web Push bildirimi
│   │   │
│   │   └── models/
│   │       ├── user.py
│   │       ├── job.py
│   │       ├── quota.py
│   │       ├── audit.py
│   │       └── glossary.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_pdf_validator.py
│   │   │   ├── test_quota.py
│   │   │   ├── test_capacity.py
│   │   │   └── test_glossary.py
│   │   └── integration/
│   │       ├── test_upload_flow.py
│   │       ├── test_sse_stream.py
│   │       └── test_admin_api.py
│   │
│   ├── alembic/                 ← DB migration
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         ← ana sayfa (upload + split view)
│   │   │   ├── history/         ← kullanıcı geçmişi
│   │   │   └── admin/           ← admin panel sayfaları
│   │   │
│   │   ├── components/
│   │   │   ├── PDFViewer/       ← PDF.js wrapper
│   │   │   ├── TranslationPanel/← SSE stream + yazı efekti
│   │   │   ├── UploadZone/      ← drag & drop + validation UI
│   │   │   ├── QuotaBar/        ← günlük/aylık kota göstergesi
│   │   │   ├── JobProgress/     ← kuyruk pozisyonu + ilerleme
│   │   │   └── admin/
│   │   │       ├── Dashboard/
│   │   │       ├── UserManagement/
│   │   │       ├── CapacityPanel/
│   │   │       ├── ReportsPanel/
│   │   │       └── AuditLog/
│   │   │
│   │   ├── hooks/
│   │   │   ├── useSSE.ts        ← SSE bağlantısı
│   │   │   ├── useQuota.ts      ← kota durumu
│   │   │   └── useCapacity.ts   ← model metrikleri
│   │   │
│   │   └── lib/
│   │       ├── api.ts           ← backend API client
│   │       └── auth.ts          ← Authentik session
│   │
│   ├── __tests__/
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│   ├── plans/                   ← @writing-plans çıktıları buraya
│   ├── architecture.md
│   └── api.md
│
└── scripts/
    ├── seed_glossary.py         ← ilk glossary yükleme
    └── create_admin.py          ← ilk admin kullanıcısı
```

---

## Tech Stack

| Katman | Teknoloji | Versiyon |
|--------|-----------|---------|
| Backend | FastAPI | ≥0.115 |
| Worker | Celery | ≥5.4 |
| Queue/Cache | Redis | ≥7 |
| ORM | SQLAlchemy 2 + Alembic | async |
| DB | PostgreSQL | ≥16 |
| Dosya depolama | MinIO | latest |
| Auth | Authentik SSO (OIDC/JWT) | mevcut K8s'teki |
| PDF engine | PDFMathTranslate (pdf2zh) | ≥1.9 |
| LLM | vLLM OpenAI-compatible | paipsap01:8001 |
| Frontend | Next.js 14 (App Router) | TypeScript |
| PDF render | PDF.js | ≥4 |
| Reverse proxy | Traefik | mevcut |
| Metrikler | Victoria Metrics | mevcut |
| Test (BE) | pytest + pytest-asyncio | |
| Test (FE) | Vitest + Testing Library | |

---

## Ortam Değişkenleri

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/translate_db
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=translate-files

# Authentik
AUTHENTIK_URL=https://auth.takasdom.takasbank.com.tr
AUTHENTIK_CLIENT_ID=...
AUTHENTIK_CLIENT_SECRET=...

# vLLM (sabit, değiştirme)
VLLM_BASE_URL=http://172.30.146.11:8001/v1
VLLM_API_KEY=dummy
VLLM_MODEL=Qwen/Qwen3.5-122B-A10B-FP8

# PDF Engine
PDF_ENGINE_THREAD_COUNT=4
PDF_OUTPUT_TTL_DAYS=7

# Proxy (tüm container'lara inject edilir)
HTTP_PROXY=http://10.20.1.140:8080
HTTPS_PROXY=http://10.20.1.140:8080
NO_PROXY=172.30.146.11,localhost,127.0.0.1,10.0.0.0/8

# HuggingFace mirror (DocLayout-YOLO indirme için)
HF_ENDPOINT=https://hf-mirror.com
```

---

## Kullanıcı Tipleri ve Kota Sistemi

```python
class UserTier(str, Enum):
    STANDARD    = "standard"     # Günlük: 50, Aylık: 500 sayfa
    POWER_USER  = "power_user"   # Günlük: 200, Aylık: 2000 sayfa
    VIP         = "vip"          # Sınırsız, kuyrukta en önce
    ADMIN       = "admin"        # Sınırsız, her şeye erişim

TIER_CONFIG = {
    "standard":   {"daily": 50,  "monthly": 500,  "max_file_mb": 50,  "max_pages": 100, "concurrent": 2, "priority": 3},
    "power_user": {"daily": 200, "monthly": 2000, "max_file_mb": 200, "max_pages": 300, "concurrent": 4, "priority": 2},
    "vip":        {"daily": None,"monthly": None,  "max_file_mb": 500, "max_pages": None,"concurrent": 10,"priority": 1},
    "admin":      {"daily": None,"monthly": None,  "max_file_mb": None,"max_pages": None,"concurrent": None,"priority": 0},
}
```

**VIP kuyruk mantığı:**
- VIP job kuyruğa girdiğinde priority skoru her zaman standart kullanıcıdan yüksek
- Starvation koruması: çok uzun bekleyen standard job da öncelik kazanabilir
- Çalışan job kesilmez — VIP sırada birinci olur ama mevcut işin bitmesi beklenir

---

## PDF Doğrulama Akışı (7 Adım)

Her adım kullanıcıya anlık SSE event ile bildirilir:

```python
# services/pdf_validator.py içinde bu sıra ile çalışır:

1. FORMAT_CHECK      → magic bytes: %PDF- ile başlıyor mu?
2. SIZE_CHECK        → kullanıcı tier'ına göre max MB
3. ENCRYPTION_CHECK  → PyMuPDF ile şifreli/kilitli mi?
4. PAGE_COUNT        → sayfa sayısı tespit + tier limiti kontrolü
5. QUOTA_CHECK       → günlük + aylık kota yeterli mi?
6. MALWARE_SCAN      → ClamAV (opsiyonel, mevcut değilse skip)
7. SCAN_DETECTION    → taranmış PDF mi? (OCR gerekecek mi bildirimi)

# Her adım sonucu:
{
    "step": "QUOTA_CHECK",
    "status": "failed",  # passed / failed / warning
    "message": "Günlük kotanız doldu (50/50 sayfa). Sıfırlanma: 23:47'de.",
    "details": {
        "daily_used": 50,
        "daily_limit": 50,
        "resets_at": "2026-03-18T23:59:59+03:00"
    }
}
```

---

## Model Kapasite Hesaplayıcısı

Admin aşağıdaki değerleri girer, sistem otomatik hesaplar:

```python
# Admin girdileri
class ModelConfig(BaseModel):
    total_vram_gb: float          # Örn: 286 (2×143 H200 NVL)
    model_weight_vram_gb: float   # Örn: 122 (FP8)
    context_window_tokens: int    # Örn: 32768
    kv_cache_type: str            # "fp8" | "fp16" | "int8" | "int4"
    kv_cache_vram_percent: float  # Örn: 0.40 (kalan VRAM'ın %40'ı)
    avg_page_tokens: int          # Örn: 400 (deneyimle kalibre edilir)
    avg_translation_tokens: int   # Örn: 600 (input + output)
    vllm_overhead_factor: float   # Örn: 0.7 (gerçekçi kullanım katsayısı)

# Sistem hesaplar
class CapacityResult(BaseModel):
    available_vram_gb: float          # total - model_weight
    kv_cache_vram_gb: float           # available × kv_cache_percent
    theoretical_concurrent: int       # kv_cache / avg_translation_tokens
    safe_concurrent: int              # theoretical × overhead_factor
    avg_page_seconds: float           # geçmiş joblardan ölçülür
    pages_per_hour: int               # safe_concurrent × (3600/avg_page_seconds)
    pages_per_day: int
    # Gerçek metrikler (Victoria Metrics'ten)
    actual_vram_used_gb: float
    actual_kv_cache_utilization: float
    actual_concurrent_requests: int
```

---

## SSE Event Formatı

Backend → Frontend arası tüm gerçek zamanlı iletişim:

```python
# Job durumu
{"event": "job_status",   "data": {"job_id": "...", "status": "processing", "queue_position": 2}}

# Doğrulama adımı
{"event": "validation",   "data": {"step": "PAGE_COUNT", "status": "passed", "pages": 47}}

# Sayfa başladı
{"event": "page_start",   "data": {"page": 3, "total": 47}}

# Sayfa tamamlandı (çeviri içeriğiyle)
{"event": "page_done",    "data": {"page": 3, "content": "...", "elapsed_ms": 4200}}

# Tüm iş tamamlandı
{"event": "job_complete", "data": {"job_id": "...", "download_url": "...", "total_pages": 47, "elapsed_s": 187}}

# Hata
{"event": "error",        "data": {"code": "QUOTA_EXCEEDED", "message": "...", "details": {}}}
```

---

## Admin Panel Bölümleri

### 1. Dashboard
- Anlık: aktif job sayısı, kuyruk derinliği, GPU VRAM kullanımı
- Bugün: çevrilen toplam sayfa, aktif kullanıcı, hata sayısı
- vLLM gerçek zamanlı metrikler (Victoria Metrics'ten)

### 2. Kullanıcı Yönetimi
- AD'den gelen kullanıcı listesi + tier + kota durumu + son aktivite
- Tek tıkla tier değiştirme
- Geçici VIP: "X tarihine kadar VIP" seçeneği
- Bireysel kota override
- Kullanıcı engelleme / aktifleştirme
- Bekleyen onaylar (ilk giriş pending → admin onayı)

### 3. Raporlar
- Kullanıcı bazlı: kim ne kadar kullandı
- Departman bazlı: AD OU/grup gruplama
- Zaman bazlı: günlük/haftalık/aylık grafikler
- Top 10 kullanıcı
- CSV export

### 4. İş Yönetimi
- Tüm joblar: durum, kullanıcı, dosya, sayfa, süre
- Takılan/hatalı jobları iptal et
- Öncelik değiştirme (acil işi öne çek)

### 5. Model Kapasite
- Parametre giriş formu
- Otomatik hesaplama sonuçları
- Teorik vs Gerçek karşılaştırma (vLLM metrikleri)
- VRAM görsel göstergesi

### 6. Sistem Ayarları
- Kota tip konfigürasyonu
- Max worker sayısı
- Dosya TTL süresi
- Bakım modu (kullanıcılara mesaj)

### 7. Glossary Yönetimi
- Teknik terimler CSV — UI'dan düzenle
- Ekle / düzenle / sil
- Bulk import CSV

### 8. Audit Log
- Kim ne zaman ne yaptı
- Filtrelenebilir, aranabilir
- 90 gün saklama
- CSV export

---

## Geliştirme Fazları

### Faz 1 — Temel Çeviri (MVP)
**Hedef:** Kullanıcı PDF yükler, çeviri başlar, sonuç indirilir.

- [ ] Docker Compose kurulumu (postgres, redis, minio)
- [ ] FastAPI skeleton + Authentik JWT middleware
- [ ] PDF validator (7 adım)
- [ ] MinIO upload/download
- [ ] PDFMathTranslate Python API wrapper
- [ ] Celery task (basit, sırasız)
- [ ] SSE stream endpoint
- [ ] Frontend: upload zone + PDF.js + SSE panel
- [ ] Temel kota kontrolü

**Faz 1 tamamlanma kriteri:** Tek kullanıcı PDF yükleyip indirebilir.

### Faz 2 — Kuyruk ve Çoklu Kullanıcı
**Hedef:** Eş zamanlı kullanıcılar, öncelikli kuyruk, VIP sistemi.

- [ ] Celery priority queue
- [ ] VIP kuyruk önceliklendirme
- [ ] Kuyruk pozisyonu SSE event
- [ ] Worker havuzu (kapasite hesabına göre)
- [ ] Frontend: kuyruk pozisyonu göstergesi

### Faz 3 — Kota ve Kullanıcı Yönetimi
**Hedef:** Tier sistemi, kota takibi, kullanıcı geçmişi.

- [ ] Kullanıcı tier sistemi (DB modeli)
- [ ] Günlük/aylık kota sayacı (Redis + DB)
- [ ] Geçici VIP (TTL'li override)
- [ ] Web Push bildirimi
- [ ] Frontend: kota bar + geçmiş sayfası

### Faz 4 — Admin Paneli
**Hedef:** Tam admin kontrolü.

- [ ] Dashboard + metrikler
- [ ] Kullanıcı yönetimi UI
- [ ] Model kapasite hesaplayıcı (Victoria Metrics entegrasyonu)
- [ ] Raporlar + CSV export
- [ ] Audit log
- [ ] Glossary yönetim UI
- [ ] Sistem ayarları + bakım modu

### Faz 5 — Production Hardening
- [ ] ClamAV entegrasyonu
- [ ] Rate limiting (dakikada 5 upload denemesi)
- [ ] MinIO bucket izolasyonu (kullanıcı bazlı)
- [ ] E2E test suite
- [ ] Load test (10 eş zamanlı kullanıcı)
- [ ] Runbook dokümantasyonu

---

## Test Stratejisi

**Kural: Her fonksiyon için önce test, sonra kod.**

```bash
# Backend testleri çalıştır
cd backend && pytest tests/ -v --tb=short

# Belirli modül
pytest tests/unit/test_pdf_validator.py -v

# Coverage
pytest tests/ --cov=app --cov-report=term-missing

# Frontend testleri
cd frontend && npx vitest run

# Integration (docker gerekli)
pytest tests/integration/ -v --timeout=60
```

**Test öncelikleri:**

1. `pdf_validator.py` → her doğrulama adımı için ayrı test
2. `quota.py` → kota hesaplama, edge case'ler (sıfırlama anı, tam dolu)
3. `capacity.py` → hesaplama doğruluğu
4. SSE stream → event sırası doğru mu
5. Admin API'ler → yetki kontrolleri (admin olmayan erişemez)

**Kritik test senaryoları:**

```python
# Bunlar mutlaka test edilmeli:
- Şifreli PDF yüklenirse ne olur?
- Kota tam doluyken upload edilirse?
- VIP kullanıcı kuyruğa girerken standart kullanıcı çalışıyorsa?
- 300 sayfalık PDF ortasında worker çökerse?
- Aynı kullanıcı aynı anda 3 job başlatmaya çalışırsa?
- Admin olmayan kullanıcı /admin endpoint'ine erişirse?
```

---

## Kritik Kurallar

1. **Proxy her yerde:** `HTTP_PROXY=http://10.20.1.140:8080` — tüm container'lara inject edilir. `NO_PROXY`'ye `172.30.146.11` (paipsap01) mutlaka eklenir.

2. **vLLM endpoint sabittir:** `http://172.30.146.11:8001/v1` — değiştirilmez, env'den okunur.

3. **Model adı:** `Qwen/Qwen3.5-122B-A10B-FP8` — PDF çevirisi için. Token-yoğun sayfalarda timeout'a dikkat.

4. **HF mirror:** DocLayout-YOLO modeli indirme için `HF_ENDPOINT=https://hf-mirror.com`.

5. **Türkçe font:** PDFMathTranslate Türkçe karakterler için `GoNotoKurrent-Regular.ttf` kullanır — container'da mevcut olduğu doğrulanmalı.

6. **Glossary:** `storage_network_glossary.csv` — `journal`, `pool`, `fabric`, `LDEV`, `HUR`, `GAD` vb. terimler çevrilmez. Her çeviri öncesi prompt'a inject edilir.

7. **TTL:** MinIO'daki dosyalar 7 gün sonra otomatik silinir — bucket lifecycle policy ile.

8. **Audit:** Admin işlemleri dahil her kritik eylem `audit_log` tablosuna yazılır. Silme işlemi yok — 90 gün sonra archive.

9. **Celery beat:** Gece yarısı günlük kota sıfırlama, ayın 1'i aylık kota sıfırlama. Timezone: `Europe/Istanbul`.

10. **Migrations:** Her model değişikliği için Alembic migration yazılır — `alembic revision --autogenerate` sonra gözden geçir, sakın olduğu gibi bırakma.

---

## Başlangıç Komutları

```bash
# Repoyu klonla ve kur
git clone <repo>
cd takasbank-translate
cp .env.example .env
# .env'i doldur

# Servisleri başlat
docker compose up -d postgres redis minio

# DB migration
cd backend
pip install -e ".[dev]"
alembic upgrade head

# İlk glossary ve admin
python scripts/seed_glossary.py
python scripts/create_admin.py

# Geliştirme modu
docker compose up -d  # tüm servisler
# veya
uvicorn app.main:app --reload --port 8080  # sadece backend

# Frontend
cd frontend
npm install
npm run dev
```

---

## Yeni Özellik Eklerken İzlenecek Yol

```
1. Bu CLAUDE.md'yi oku
2. docs/plans/ klasörüne bak — plan var mı?
3. Yoksa: @writing-plans skill ile plan yaz
4. Plan onaylandıktan sonra: @executing-plans ile implemente et
5. Her adımda: @test-driven-development — önce test
6. Bitti mi: @verification-before-completion — çalıştığını kanıtla
7. Commit: konvansiyonel commit mesajı (feat/fix/refactor/test/docs)
8. PR: değişiklikleri özetle
```

---

## Commit Konvansiyonu

```
feat(upload): PDF şifre kontrolü eklendi
fix(quota): gece yarısı sıfırlama timezone hatası düzeltildi
refactor(validator): 7 adım ayrı fonksiyonlara ayrıldı
test(capacity): model kapasite hesaplama edge case'leri
docs(api): upload endpoint dokümantasyonu
chore(docker): redis healthcheck eklendi
```

---

*Son güncelleme: 2026-03-18*
*Mimari kararlar için: Kenan Karakoç*
