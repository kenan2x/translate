from app.core.capacity import ModelConfig, calculate_capacity, CapacityResult


def test_calculate_capacity_basic():
    config = ModelConfig(
        total_vram_gb=286,
        model_weight_vram_gb=122,
        context_window_tokens=32768,
        kv_cache_type="fp8",
        kv_cache_vram_percent=0.40,
        avg_page_tokens=400,
        avg_translation_tokens=600,
        vllm_overhead_factor=0.7,
    )
    result = calculate_capacity(config, avg_page_seconds=4.0)

    assert result.available_vram_gb == 164.0
    assert result.kv_cache_vram_gb == 65.6
    assert result.theoretical_concurrent > 0
    assert result.safe_concurrent > 0
    assert result.safe_concurrent <= result.theoretical_concurrent
    assert result.pages_per_hour > 0
    assert result.pages_per_day == result.pages_per_hour * 24


def test_capacity_returns_at_least_one():
    config = ModelConfig(
        total_vram_gb=10,
        model_weight_vram_gb=9,
        context_window_tokens=4096,
        kv_cache_type="fp16",
        kv_cache_vram_percent=0.1,
        avg_page_tokens=400,
        avg_translation_tokens=600,
        vllm_overhead_factor=0.5,
    )
    result = calculate_capacity(config)
    assert result.safe_concurrent >= 1


def test_capacity_result_fields():
    config = ModelConfig(
        total_vram_gb=286,
        model_weight_vram_gb=122,
        context_window_tokens=32768,
        kv_cache_type="fp8",
        kv_cache_vram_percent=0.40,
        avg_page_tokens=400,
        avg_translation_tokens=600,
        vllm_overhead_factor=0.7,
    )
    result = calculate_capacity(config)
    assert isinstance(result, CapacityResult)
    assert result.actual_vram_used_gb is None  # Not from metrics yet
    assert result.actual_concurrent_requests is None
