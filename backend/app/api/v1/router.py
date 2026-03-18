from fastapi import APIRouter

from app.api.v1.upload import router as upload_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.download import router as download_router
from app.api.v1.history import router as history_router

v1_router = APIRouter(tags=["v1"])

v1_router.include_router(upload_router)
v1_router.include_router(jobs_router)
v1_router.include_router(download_router)
v1_router.include_router(history_router)


@v1_router.get("/status")
async def status():
    return {"api": "v1", "status": "ok"}
