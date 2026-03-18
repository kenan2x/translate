from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    total_vram_gb: float
    model_weight_vram_gb: float
    context_window_tokens: int
    kv_cache_type: str  # "fp8" | "fp16" | "int8" | "int4"
    kv_cache_vram_percent: float
    avg_page_tokens: int
    avg_translation_tokens: int
    vllm_overhead_factor: float


@dataclass
class CapacityResult:
    available_vram_gb: float
    kv_cache_vram_gb: float
    theoretical_concurrent: int
    safe_concurrent: int
    avg_page_seconds: float
    pages_per_hour: int
    pages_per_day: int
    # Actuals from metrics (optional)
    actual_vram_used_gb: Optional[float] = None
    actual_kv_cache_utilization: Optional[float] = None
    actual_concurrent_requests: Optional[int] = None


# KV cache bytes per token by type
KV_BYTES_PER_TOKEN = {
    "fp16": 4,   # 2 bytes key + 2 bytes value per head
    "fp8": 2,
    "int8": 2,
    "int4": 1,
}


def calculate_capacity(config: ModelConfig, avg_page_seconds: float = 4.0) -> CapacityResult:
    """Calculate model capacity based on hardware config."""
    available_vram = config.total_vram_gb - config.model_weight_vram_gb
    kv_cache_vram = available_vram * config.kv_cache_vram_percent

    # Theoretical concurrent: kv_cache_vram / (tokens_per_request * bytes_per_token)
    bytes_per_token = KV_BYTES_PER_TOKEN.get(config.kv_cache_type, 4)
    kv_per_request_gb = (config.avg_translation_tokens * bytes_per_token * config.context_window_tokens) / (1024**3)

    if kv_per_request_gb > 0:
        theoretical = int(kv_cache_vram / kv_per_request_gb)
    else:
        theoretical = 1

    safe_concurrent = max(1, int(theoretical * config.vllm_overhead_factor))

    if avg_page_seconds > 0:
        pages_per_hour = int(safe_concurrent * (3600 / avg_page_seconds))
    else:
        pages_per_hour = 0

    pages_per_day = pages_per_hour * 24

    return CapacityResult(
        available_vram_gb=round(available_vram, 2),
        kv_cache_vram_gb=round(kv_cache_vram, 2),
        theoretical_concurrent=theoretical,
        safe_concurrent=safe_concurrent,
        avg_page_seconds=avg_page_seconds,
        pages_per_hour=pages_per_hour,
        pages_per_day=pages_per_day,
    )
