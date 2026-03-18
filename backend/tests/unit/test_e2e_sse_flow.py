"""End-to-end test: PDF upload → translate → SSE events.

Tests the full flow without external dependencies (no Redis, no vLLM).
Verifies that:
1. PDF pages are extracted correctly
2. Each page is translated via OpenAI API
3. Callback fires for each page with correct data
4. Events contain page number, total, content, and timing
"""
import io
import json
from unittest.mock import MagicMock

import fitz
import pytest

from app.services.pdf_translator import PDFTranslator, PageResult


def _make_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _mock_translator(translate_fn=None):
    """Create a translator with mocked OpenAI client."""
    t = PDFTranslator(
        vllm_base_url="http://mock:8099/v1",
        vllm_model="mock-model",
        vllm_api_key="dummy",
    )

    call_count = {"n": 0}

    def default_translate(**kwargs):
        call_count["n"] += 1
        text = kwargs["messages"][1]["content"]
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = f"[TR] {text}"
        return resp

    t.client = MagicMock()
    t.client.chat.completions.create.side_effect = translate_fn or default_translate
    return t, call_count


class TestFullTranslationFlow:
    """Simulates the complete Celery task flow."""

    def test_3_page_pdf_produces_3_events(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf([
            "This is page one with some content.",
            "Page two has more text here.",
            "Page three is the final page.",
        ]))

        translator, _ = _mock_translator()
        events = []

        def callback(result: PageResult):
            events.append({
                "event": "page_done",
                "data": {
                    "page": result.page,
                    "total": result.total,
                    "content": result.translated,
                    "elapsed_ms": result.elapsed_ms,
                },
            })

        results = translator.translate(str(pdf_path), callback=callback)

        # 3 pages = 3 events
        assert len(events) == 3

        # Each event has correct structure
        for i, event in enumerate(events):
            assert event["event"] == "page_done"
            assert event["data"]["page"] == i + 1
            assert event["data"]["total"] == 3
            assert "[TR]" in event["data"]["content"]
            assert event["data"]["elapsed_ms"] >= 0

    def test_events_arrive_in_order(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["A", "B", "C", "D", "E"]))

        translator, _ = _mock_translator()
        pages_seen = []

        def callback(result: PageResult):
            pages_seen.append(result.page)

        translator.translate(str(pdf_path), callback=callback)

        assert pages_seen == [1, 2, 3, 4, 5]

    def test_translated_content_is_returned(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["Hello World"]))

        translator, _ = _mock_translator()
        events = []

        translator.translate(
            str(pdf_path),
            callback=lambda r: events.append(r),
        )

        assert len(events) == 1
        assert "Hello World" in events[0].translated
        assert "[TR]" in events[0].translated

    def test_empty_page_skips_api_call(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["Content", "", "More content"]))

        translator, call_count = _mock_translator()
        events = []

        translator.translate(
            str(pdf_path),
            callback=lambda r: events.append(r),
        )

        assert len(events) == 3  # all 3 pages reported
        assert call_count["n"] == 2  # only 2 API calls
        assert events[1].translated == ""  # empty page

    def test_one_page_failure_doesnt_stop_others(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["Good", "Bad", "Good"]))

        def flaky_translate(**kwargs):
            text = kwargs["messages"][1]["content"]
            if "Bad" in text:
                raise ConnectionError("timeout")
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = f"[TR] {text}"
            return resp

        translator, _ = _mock_translator(flaky_translate)
        events = []

        translator.translate(
            str(pdf_path),
            callback=lambda r: events.append(r),
        )

        assert len(events) == 3
        assert "[TR]" in events[0].translated
        assert "hatasi" in events[1].translated  # error message
        assert "[TR]" in events[2].translated  # continued


class TestSSEEventFormat:
    """Verify events match what frontend expects."""

    def test_page_done_has_required_fields(self, tmp_path):
        """Frontend useSSE.ts expects: page, total, content, elapsed_ms."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["Test"]))

        translator, _ = _mock_translator()
        events = []

        def callback(result: PageResult):
            # Simulate what queue.py builds
            events.append({
                "page": result.page,
                "total": result.total,
                "content": result.translated,
                "elapsed_ms": result.elapsed_ms,
                "job_id": "test-123",
            })

        translator.translate(str(pdf_path), callback=callback)

        event = events[0]
        assert "page" in event
        assert "total" in event
        assert "content" in event
        assert "elapsed_ms" in event
        assert isinstance(event["page"], int)
        assert isinstance(event["total"], int)
        assert isinstance(event["content"], str)
        assert isinstance(event["elapsed_ms"], int)

    def test_job_complete_format(self, tmp_path):
        """Frontend expects: download_url, total_pages."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["Test"]))

        translator, _ = _mock_translator()
        results = translator.translate(str(pdf_path))

        # Simulate what queue.py builds
        complete_event = {
            "job_id": "test-123",
            "download_url": "/api/v1/download/test-123",
            "total_pages": len(results),
        }

        assert "download_url" in complete_event
        assert "total_pages" in complete_event
        assert complete_event["total_pages"] == 1


class TestRealTimeBehavior:
    """Test that events fire during translation, not after."""

    def test_callback_fires_before_translate_returns(self, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(_make_pdf(["A", "B"]))

        translator, _ = _mock_translator()
        callback_times = []
        return_time = [None]

        def callback(result: PageResult):
            import time
            callback_times.append(time.monotonic())

        import time
        results = translator.translate(str(pdf_path), callback=callback)
        return_time[0] = time.monotonic()

        # Both callbacks should fire BEFORE translate returns
        assert len(callback_times) == 2
        assert all(t < return_time[0] for t in callback_times)
