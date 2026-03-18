import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import fitz  # PyMuPDF
import pytest

from app.services.pdf_translator import SYSTEM_PROMPT, PDFTranslator, PageResult


def _create_test_pdf(path: Path, pages: list[str]) -> str:
    """Create a real PDF with given page texts using PyMuPDF."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return str(path)


# --- PDFTranslator init ---


def test_translator_init():
    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
        vllm_api_key="test-key",
        thread_count=2,
    )
    assert t.vllm_base_url == "http://localhost:8001/v1"
    assert t.vllm_model == "test-model"
    assert t.vllm_api_key == "test-key"
    assert t.thread_count == 2
    assert t.client is not None


# --- extract_pages ---


def test_extract_pages_single_page(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Hello World"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )
    pages = t.extract_pages(str(pdf_path))

    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "Hello World" in pages[0]["text"]


def test_extract_pages_multiple_pages(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Page one", "Page two", "Page three"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )
    pages = t.extract_pages(str(pdf_path))

    assert len(pages) == 3
    assert pages[0]["page"] == 1
    assert pages[1]["page"] == 2
    assert pages[2]["page"] == 3
    assert "Page one" in pages[0]["text"]
    assert "Page three" in pages[2]["text"]


def test_extract_pages_empty_page(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Content", "", "More content"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )
    pages = t.extract_pages(str(pdf_path))

    assert len(pages) == 3
    assert pages[1]["text"] == ""  # empty page


# --- translate_page ---


def test_translate_page_calls_openai(tmp_path):
    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Merhaba Dunya"

    t.client = MagicMock()
    t.client.chat.completions.create.return_value = mock_response

    result = t.translate_page("Hello World")

    assert result == "Merhaba Dunya"
    t.client.chat.completions.create.assert_called_once()

    call_kwargs = t.client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][0]["content"] == SYSTEM_PROMPT
    assert call_kwargs["messages"][1]["content"] == "Hello World"


def test_translate_page_empty_text():
    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )
    t.client = MagicMock()

    # Empty text should return as-is without calling API
    assert t.translate_page("") == ""
    assert t.translate_page("  ") == "  "
    assert t.translate_page("ab") == "ab"
    t.client.chat.completions.create.assert_not_called()


def test_translate_page_none_response():
    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None

    t.client = MagicMock()
    t.client.chat.completions.create.return_value = mock_response

    result = t.translate_page("Hello World")
    assert result == ""


# --- translate (full flow) ---


def test_translate_full_flow(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Hello", "World"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    call_count = {"n": 0}

    def mock_create(**kwargs):
        call_count["n"] += 1
        resp = MagicMock()
        text = kwargs["messages"][1]["content"]
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = f"TR:{text}"
        return resp

    t.client = MagicMock()
    t.client.chat.completions.create.side_effect = mock_create

    callback_results = []
    results = t.translate(str(pdf_path), callback=lambda r: callback_results.append(r))

    assert len(results) == 2
    assert results[0].page == 1
    assert results[0].total == 2
    assert "TR:" in results[0].translated
    assert results[0].elapsed_ms >= 0
    assert results[1].page == 2

    # Callback called for each page
    assert len(callback_results) == 2
    assert callback_results[0].page == 1
    assert callback_results[1].page == 2


def test_translate_without_callback(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Hello"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Merhaba"

    t.client = MagicMock()
    t.client.chat.completions.create.return_value = mock_response

    # Should not raise even without callback
    results = t.translate(str(pdf_path))
    assert len(results) == 1
    assert results[0].translated == "Merhaba"


def test_translate_page_error_handled(tmp_path):
    """If one page fails, it should not crash the whole translation."""
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Good page", "Bad page", "Good again"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    call_count = {"n": 0}

    def mock_create(**kwargs):
        call_count["n"] += 1
        text = kwargs["messages"][1]["content"]
        if "Bad" in text:
            raise ConnectionError("vLLM timeout")
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = f"TR:{text}"
        return resp

    t.client = MagicMock()
    t.client.chat.completions.create.side_effect = mock_create

    results = t.translate(str(pdf_path))

    assert len(results) == 3
    assert "TR:" in results[0].translated
    assert "Ceviri hatasi" in results[1].translated  # error handled
    assert "TR:" in results[2].translated  # continued after error


def test_translate_empty_pages_skipped(tmp_path):
    """Empty pages should not call the API."""
    pdf_path = tmp_path / "test.pdf"
    _create_test_pdf(pdf_path, ["Content", "", "More"])

    t = PDFTranslator(
        vllm_base_url="http://localhost:8001/v1",
        vllm_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Cevirildi"

    t.client = MagicMock()
    t.client.chat.completions.create.return_value = mock_response

    results = t.translate(str(pdf_path))

    assert len(results) == 3
    # Only 2 API calls (empty page skipped)
    assert t.client.chat.completions.create.call_count == 2
    assert results[1].translated == ""  # empty page stays empty


# --- PageResult dataclass ---


def test_page_result_dataclass():
    r = PageResult(
        page=1, total=5, original="Hello", translated="Merhaba", elapsed_ms=150,
    )
    assert r.page == 1
    assert r.total == 5
    assert r.original == "Hello"
    assert r.translated == "Merhaba"
    assert r.elapsed_ms == 150
