from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "translate-files"

    # Auth bypass for dev/test (set AUTH_DISABLED=true to skip Authentik)
    AUTH_DISABLED: bool = False
    DEV_USER_EMAIL: str = "dev@takasbank.com.tr"
    DEV_USER_NAME: str = "Dev User"
    DEV_USER_TIER: str = "admin"

    # Authentik (optional when AUTH_DISABLED=true)
    AUTHENTIK_URL: str = ""
    AUTHENTIK_CLIENT_ID: str = ""
    AUTHENTIK_CLIENT_SECRET: str = ""

    # vLLM (defaults are fixed, don't change)
    VLLM_BASE_URL: str = "http://172.30.146.11:8001/v1"
    VLLM_API_KEY: str = "dummy"
    VLLM_MODEL: str = "Qwen/Qwen3.5-122B-A10B-FP8"

    # PDF Engine
    PDF_ENGINE_THREAD_COUNT: int = 4
    PDF_OUTPUT_TTL_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env")
