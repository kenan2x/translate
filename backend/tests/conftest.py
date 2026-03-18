import pytest
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test_db",
        REDIS_URL="redis://localhost:6379/1",
        MINIO_ENDPOINT="localhost:9000",
        MINIO_ACCESS_KEY="testkey",
        MINIO_SECRET_KEY="testsecret",
        AUTHENTIK_URL="https://auth.test.com",
        AUTHENTIK_CLIENT_ID="test-client",
        AUTHENTIK_CLIENT_SECRET="test-secret",
    )
