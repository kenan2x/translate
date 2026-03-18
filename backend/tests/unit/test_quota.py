from app.core.quota import QuotaService, TIER_CONFIG
from app.models.user import UserTier


def test_tier_config_standard():
    cfg = TIER_CONFIG[UserTier.STANDARD.value]
    assert cfg["daily"] == 50
    assert cfg["monthly"] == 500
    assert cfg["max_file_mb"] == 50
    assert cfg["max_pages"] == 100
    assert cfg["concurrent"] == 2
    assert cfg["priority"] == 3


def test_tier_config_power_user():
    cfg = TIER_CONFIG[UserTier.POWER_USER.value]
    assert cfg["daily"] == 200
    assert cfg["monthly"] == 2000


def test_tier_config_vip_unlimited():
    cfg = TIER_CONFIG[UserTier.VIP.value]
    assert cfg["daily"] is None
    assert cfg["monthly"] is None


def test_tier_config_admin_unlimited():
    cfg = TIER_CONFIG[UserTier.ADMIN.value]
    assert cfg["daily"] is None
    assert cfg["monthly"] is None
    assert cfg["max_file_mb"] is None
    assert cfg["max_pages"] is None


def test_check_quota_passes_when_enough():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=10,
        daily_used=30,
        monthly_used=400,
    )
    assert result.allowed is True


def test_check_quota_fails_daily():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=10,
        daily_used=45,
        monthly_used=0,
    )
    assert result.allowed is False
    assert "daily" in result.reason.lower()


def test_check_quota_fails_monthly():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=10,
        daily_used=0,
        monthly_used=495,
    )
    assert result.allowed is False
    assert "monthly" in result.reason.lower()


def test_check_quota_exact_daily_limit():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=5,
        daily_used=45,
        monthly_used=0,
    )
    assert result.allowed is True


def test_check_quota_exact_daily_over_by_one():
    result = QuotaService.check(
        tier=UserTier.STANDARD,
        pages_requested=6,
        daily_used=45,
        monthly_used=0,
    )
    assert result.allowed is False


def test_check_quota_vip_always_passes():
    result = QuotaService.check(
        tier=UserTier.VIP,
        pages_requested=9999,
        daily_used=9999,
        monthly_used=9999,
    )
    assert result.allowed is True


def test_check_quota_admin_always_passes():
    result = QuotaService.check(
        tier=UserTier.ADMIN,
        pages_requested=99999,
        daily_used=99999,
        monthly_used=99999,
    )
    assert result.allowed is True


def test_get_tier_config():
    cfg = QuotaService.get_tier_config(UserTier.STANDARD)
    assert cfg["daily"] == 50
