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
