#!/usr/bin/env python3
"""End-to-end SSE test — uploads a PDF and verifies real-time events.

Usage:
    python scripts/test_e2e_sse.py                          # default localhost:8080
    python scripts/test_e2e_sse.py http://172.30.146.31:9775

Creates a test PDF, uploads it, connects to SSE, and prints every event.
Exits with 0 if page_done events with content are received.
"""
import io
import json
import sys
import threading
import time

import fitz  # PyMuPDF
import httpx


def create_test_pdf(num_pages: int = 3) -> bytes:
    """Create a real PDF with text on each page."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"This is page {i + 1}. It contains sample text for translation testing.\n"
            f"Technical terms like API, HTTP, and SSL should remain untranslated.",
            fontsize=12,
        )
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def main():
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    num_pages = 3
    timeout = 120  # max seconds to wait

    print(f"=== E2E SSE Test ===")
    print(f"Backend: {backend_url}")
    print(f"Test PDF: {num_pages} pages")
    print()

    # 1. Health check
    print("[1/4] Health check...")
    try:
        r = httpx.get(f"{backend_url}/health", timeout=5)
        print(f"  {r.status_code} — {r.text}")
        assert r.status_code == 200
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 2. Upload PDF
    print("[2/4] Uploading test PDF...")
    pdf_data = create_test_pdf(num_pages)
    try:
        r = httpx.post(
            f"{backend_url}/api/v1/upload",
            files={"file": ("test.pdf", pdf_data, "application/pdf")},
            timeout=30,
        )
        print(f"  {r.status_code} — {r.text}")
        assert r.status_code == 202
        job_id = r.json()["job_id"]
        print(f"  job_id: {job_id}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 3. Connect to SSE and collect events
    print(f"[3/4] Connecting to SSE stream for job {job_id}...")
    events = []
    page_done_events = []
    complete = threading.Event()

    def listen_sse():
        try:
            with httpx.stream(
                "GET",
                f"{backend_url}/api/v1/jobs/{job_id}",
                timeout=httpx.Timeout(timeout, connect=10),
            ) as response:
                buffer = ""
                current_event = "message"
                for chunk in response.iter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line.startswith("event:"):
                            current_event = line[6:].strip()
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                data = data_str

                            event_info = {"event": current_event, "data": data}
                            events.append(event_info)

                            timestamp = time.strftime("%H:%M:%S")
                            print(f"  [{timestamp}] event={current_event} data={json.dumps(data, ensure_ascii=False)[:120]}")

                            if current_event == "page_done":
                                page_done_events.append(data)
                            if current_event in ("job_complete", "error"):
                                complete.set()
                                return

                            current_event = "message"
                        elif line == "":
                            current_event = "message"
        except Exception as e:
            print(f"  SSE error: {e}")
            complete.set()

    thread = threading.Thread(target=listen_sse, daemon=True)
    thread.start()
    complete.wait(timeout=timeout)
    thread.join(timeout=2)

    # 4. Verify results
    print()
    print(f"[4/4] Results:")
    print(f"  Total events received: {len(events)}")
    print(f"  page_done events: {len(page_done_events)}")

    # Check page_done events have content
    has_content = any(
        isinstance(e.get("content"), str) and len(e.get("content", "")) > 0
        for e in page_done_events
    )

    has_complete = any(e["event"] == "job_complete" for e in events)
    has_error = any(e["event"] == "error" for e in events)

    print(f"  page_done with content: {has_content}")
    print(f"  job_complete received: {has_complete}")
    print(f"  error received: {has_error}")
    print()

    if has_error:
        error_data = next(e["data"] for e in events if e["event"] == "error")
        print(f"  ERROR: {json.dumps(error_data, ensure_ascii=False)}")
        print()

    if has_content and has_complete and not has_error:
        print("=== PASS: Real-time SSE events working ===")

        # Print translated content
        print()
        for e in page_done_events:
            page = e.get("page", "?")
            total = e.get("total", "?")
            content = e.get("content", "")[:80]
            elapsed = e.get("elapsed_ms", "?")
            print(f"  Sayfa {page}/{total} ({elapsed}ms): {content}")

        sys.exit(0)
    elif len(page_done_events) == 0:
        print("=== FAIL: No page_done events received ===")
        print("  Possible causes:")
        print("  - Celery worker not running or not processing")
        print("  - vLLM unreachable from celery worker")
        print("  - SSE buffering issue")
        sys.exit(1)
    elif not has_content:
        print("=== FAIL: page_done events have no content ===")
        sys.exit(1)
    else:
        print("=== PARTIAL: Events received but job did not complete ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
