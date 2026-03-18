from app.models.user import User, UserTier
from app.models.job import Job, JobStatus
from app.models.quota import QuotaUsage, PeriodType


def test_user_tier_enum():
    assert UserTier.STANDARD == "standard"
    assert UserTier.POWER_USER == "power_user"
    assert UserTier.VIP == "vip"
    assert UserTier.ADMIN == "admin"


def test_job_status_enum():
    assert JobStatus.PENDING == "pending"
    assert JobStatus.PROCESSING == "processing"
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"
    assert JobStatus.CANCELLED == "cancelled"


def test_period_type_enum():
    assert PeriodType.DAILY == "daily"
    assert PeriodType.MONTHLY == "monthly"


def test_user_model_columns():
    cols = {c.name for c in User.__table__.columns}
    assert "id" in cols
    assert "external_id" in cols
    assert "email" in cols
    assert "display_name" in cols
    assert "tier" in cols
    assert "is_active" in cols
    assert "created_at" in cols


def test_job_model_columns():
    cols = {c.name for c in Job.__table__.columns}
    assert "id" in cols
    assert "user_id" in cols
    assert "original_filename" in cols
    assert "status" in cols
    assert "page_count" in cols
    assert "translated_pages" in cols
    assert "celery_task_id" in cols


def test_quota_usage_model_columns():
    cols = {c.name for c in QuotaUsage.__table__.columns}
    assert "user_id" in cols
    assert "date" in cols
    assert "pages_used" in cols
    assert "period_type" in cols
