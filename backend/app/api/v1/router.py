from fastapi import APIRouter

v1_router = APIRouter(tags=["v1"])


@v1_router.get("/status")
async def status():
    return {"api": "v1", "status": "ok"}
