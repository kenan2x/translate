from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.pdf_translator import PDFTranslator


def test_translate_fallback_without_pdf2zh(tmp_path):
    """When pdf2zh is not installed, fallback copies the file."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test content")
    output_dir = tmp_path / "output"

    translator = PDFTranslator(
        vllm_base_url="http://172.30.146.11:8001/v1",
        vllm_model="Qwen/Qwen3.5-122B-A10B-FP8",
    )

    # Force ImportError by patching the import inside translate
    original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

    def mock_import(name, *args, **kwargs):
        if name == "pdf2zh":
            raise ImportError("No module named 'pdf2zh'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        result = translator.translate(str(input_pdf), str(output_dir))

    assert result.endswith("_tr.pdf")
    assert Path(result).exists()


def test_translate_calls_callback(tmp_path):
    """Callback is called during fallback translation."""
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.4 test content")
    output_dir = tmp_path / "output"

    pages_reported = []

    def callback(page, total):
        pages_reported.append((page, total))

    translator = PDFTranslator(
        vllm_base_url="http://172.30.146.11:8001/v1",
        vllm_model="Qwen/Qwen3.5-122B-A10B-FP8",
    )

    original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

    def mock_import(name, *args, **kwargs):
        if name == "pdf2zh":
            raise ImportError("No module named 'pdf2zh'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        translator.translate(str(input_pdf), str(output_dir), callback=callback)

    assert len(pages_reported) > 0
    assert pages_reported[0] == (1, 1)


def test_translator_init():
    translator = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
        vllm_api_key="test-key",
        thread_count=2,
    )
    assert translator.vllm_base_url == "http://localhost:8001/v1"
    assert translator.vllm_model == "test-model"
    assert translator.thread_count == 2
