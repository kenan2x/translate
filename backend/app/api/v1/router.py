from fastapi import APIRouter

from app.api.v1.upload import router as upload_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.download import router as download_router
from app.api.v1.history import router as history_router
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.admin.quotas import router as admin_quotas_router
from app.api.v1.admin.jobs import router as admin_jobs_router
from app.api.v1.admin.capacity import router as admin_capacity_router
from app.api.v1.admin.reports import router as admin_reports_router
from app.api.v1.admin.audit import router as admin_audit_router
from app.api.v1.admin.glossary import router as admin_glossary_router
from app.api.v1.admin.settings import router as admin_settings_router

v1_router = APIRouter(tags=["v1"])

v1_router.include_router(upload_router)
v1_router.include_router(jobs_router)
v1_router.include_router(download_router)
v1_router.include_router(history_router)

# Admin routes
v1_router.include_router(admin_users_router)
v1_router.include_router(admin_quotas_router)
v1_router.include_router(admin_jobs_router)
v1_router.include_router(admin_capacity_router)
v1_router.include_router(admin_reports_router)
v1_router.include_router(admin_audit_router)
v1_router.include_router(admin_glossary_router)
v1_router.include_router(admin_settings_router)


@v1_router.get("/status")
async def status():
    return {"api": "v1", "status": "ok"}
