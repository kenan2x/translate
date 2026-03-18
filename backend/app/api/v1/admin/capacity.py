from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.admin.users import require_admin
from app.core.capacity import ModelConfig, calculate_capacity

router = APIRouter(prefix="/admin/capacity", tags=["admin"])


class CapacityRequest(BaseModel):
    total_vram_gb: float = 286
    model_weight_vram_gb: float = 122
    context_window_tokens: int = 32768
    kv_cache_type: str = "fp8"
    kv_cache_vram_percent: float = 0.40
    avg_page_tokens: int = 400
    avg_translation_tokens: int = 600
    vllm_overhead_factor: float = 0.7
    avg_page_seconds: float = 4.0


@router.post("/calculate")
async def calculate(
    body: CapacityRequest,
    admin: Dict = Depends(require_admin),
):
    """Calculate model capacity from parameters."""
    config = ModelConfig(
        total_vram_gb=body.total_vram_gb,
        model_weight_vram_gb=body.model_weight_vram_gb,
        context_window_tokens=body.context_window_tokens,
        kv_cache_type=body.kv_cache_type,
        kv_cache_vram_percent=body.kv_cache_vram_percent,
        avg_page_tokens=body.avg_page_tokens,
        avg_translation_tokens=body.avg_translation_tokens,
        vllm_overhead_factor=body.vllm_overhead_factor,
    )
    result = calculate_capacity(config, avg_page_seconds=body.avg_page_seconds)
    return {
        "available_vram_gb": result.available_vram_gb,
        "kv_cache_vram_gb": result.kv_cache_vram_gb,
        "theoretical_concurrent": result.theoretical_concurrent,
        "safe_concurrent": result.safe_concurrent,
        "avg_page_seconds": result.avg_page_seconds,
        "pages_per_hour": result.pages_per_hour,
        "pages_per_day": result.pages_per_day,
    }


@router.get("/metrics")
async def get_vllm_metrics(admin: Dict = Depends(require_admin)):
    """Get real-time vLLM metrics from Victoria Metrics."""
    # TODO: Query Victoria Metrics for actual vLLM metrics
    return {
        "actual_vram_used_gb": None,
        "actual_kv_cache_utilization": None,
        "actual_concurrent_requests": None,
        "gpu_utilization_percent": None,
    }
