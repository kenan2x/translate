import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.auth import get_current_user


def _make_app_with_auth(user_data):
    app = create_app()

    async def mock_auth():
        return user_data

    app.dependency_overrides[get_current_user] = mock_auth
    return app


@pytest.fixture
def admin_client():
    app = _make_app_with_auth({
        "sub": "admin-1", "email": "admin@test.com",
        "name": "Admin", "groups": ["admin"], "tier": "admin"
    })
    return TestClient(app)


@pytest.fixture
def user_client():
    app = _make_app_with_auth({
        "sub": "user-1", "email": "user@test.com",
        "name": "User", "groups": [], "tier": "standard"
    })
    return TestClient(app)


class TestAdminAccess:
    def test_admin_can_list_users(self, admin_client):
        resp = admin_client.get("/api/v1/admin/users")
        assert resp.status_code == 200

    def test_non_admin_blocked(self, user_client):
        resp = user_client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    def test_non_admin_blocked_audit(self, user_client):
        resp = user_client.get("/api/v1/admin/audit")
        assert resp.status_code == 403

    def test_non_admin_blocked_settings(self, user_client):
        resp = user_client.get("/api/v1/admin/settings")
        assert resp.status_code == 403


class TestAdminUsers:
    def test_update_tier(self, admin_client):
        resp = admin_client.patch("/api/v1/admin/users/1/tier", json={"tier": "vip"})
        assert resp.status_code == 200
        assert resp.json()["tier"] == "vip"

    def test_update_tier_invalid(self, admin_client):
        resp = admin_client.patch("/api/v1/admin/users/1/tier", json={"tier": "mega"})
        assert resp.status_code == 422

    def test_grant_temp_vip(self, admin_client):
        resp = admin_client.post(
            "/api/v1/admin/users/1/temp-vip",
            json={"until": "2026-04-01T00:00:00"}
        )
        assert resp.status_code == 200

    def test_block_user(self, admin_client):
        resp = admin_client.post("/api/v1/admin/users/1/block")
        assert resp.status_code == 200
        assert resp.json()["blocked"] is True


class TestAdminCapacity:
    def test_calculate_capacity(self, admin_client):
        resp = admin_client.post("/api/v1/admin/capacity/calculate", json={
            "total_vram_gb": 286,
            "model_weight_vram_gb": 122,
            "context_window_tokens": 32768,
            "kv_cache_type": "fp8",
            "kv_cache_vram_percent": 0.4,
            "avg_page_tokens": 400,
            "avg_translation_tokens": 600,
            "vllm_overhead_factor": 0.7,
            "avg_page_seconds": 4.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["available_vram_gb"] == 164.0
        assert data["safe_concurrent"] > 0
        assert data["pages_per_hour"] > 0


class TestAdminGlossary:
    def test_list_terms(self, admin_client):
        resp = admin_client.get("/api/v1/admin/glossary")
        assert resp.status_code == 200

    def test_add_term(self, admin_client):
        resp = admin_client.post("/api/v1/admin/glossary", json={
            "source_term": "LDEV",
            "target_term": "LDEV",
            "do_not_translate": True,
        })
        assert resp.status_code == 200
        assert resp.json()["created"] is True

    def test_delete_term(self, admin_client):
        resp = admin_client.delete("/api/v1/admin/glossary/1")
        assert resp.status_code == 200


class TestAdminReports:
    def test_usage_report(self, admin_client):
        resp = admin_client.get("/api/v1/admin/reports/usage")
        assert resp.status_code == 200

    def test_csv_export(self, admin_client):
        resp = admin_client.get("/api/v1/admin/reports/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


class TestAdminAudit:
    def test_audit_log(self, admin_client):
        resp = admin_client.get("/api/v1/admin/audit")
        assert resp.status_code == 200

    def test_audit_csv_export(self, admin_client):
        resp = admin_client.get("/api/v1/admin/audit/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


class TestAdminSettings:
    def test_get_settings(self, admin_client):
        resp = admin_client.get("/api/v1/admin/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "maintenance_mode" in data
        assert "tier_config" in data

    def test_update_settings(self, admin_client):
        resp = admin_client.patch("/api/v1/admin/settings", json={
            "maintenance_mode": True,
            "maintenance_message": "Bakim yapiliyor"
        })
        assert resp.status_code == 200
