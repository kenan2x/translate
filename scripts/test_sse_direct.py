#!/usr/bin/env python3
"""Direct SSE endpoint test — bypasses frontend, tests backend SSE only.

Usage:
    python scripts/test_sse_direct.py                          # default localhost:8080
    python scripts/test_sse_direct.py http://172.30.146.31:9775

This script:
1. Uploads a PDF to the backend
2. Immediately connects to the SSE endpoint
3. Prints every raw SSE event as it arrives
4. Verifies event format matches what the frontend expects

This helps diagnose whether the issue is in the backend (SSE not sending)
or the frontend (not rendering received events).
"""
import io
import json
import sys
import threading
import time

import fitz  # PyMuPDF
import httpx


def create_test_pdf(num_pages: int = 3) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Page {i + 1}: Sample text for translation testing.\n"
            f"Technical terms like API, HTTP, SSL should remain.",
            fontsize=12,
        )
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def main():
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    num_pages = 3

    print("=" * 60)
    print("DIRECT SSE BACKEND TEST")
    print("=" * 60)
    print(f"Backend: {backend_url}")
    print(f"Test PDF: {num_pages} pages")
    print()

    # 1. Health check
    print("[1/3] Health check...")
    try:
        r = httpx.get(f"{backend_url}/health", timeout=5)
        print(f"  Status: {r.status_code} — {r.text}")
        if r.status_code != 200:
            print("  FAIL: Backend not healthy")
            sys.exit(1)
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 2. Upload PDF
    print("[2/3] Uploading PDF...")
    pdf_data = create_test_pdf(num_pages)
    try:
        r = httpx.post(
            f"{backend_url}/api/v1/upload",
            files={"file": ("test.pdf", pdf_data, "application/pdf")},
            timeout=30,
        )
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text}")
        if r.status_code not in (200, 201, 202):
            print(f"  FAIL: Upload returned {r.status_code}")
            sys.exit(1)
        job_id = r.json()["job_id"]
        print(f"  job_id: {job_id}")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 3. Connect to SSE and inspect raw events
    print(f"\n[3/3] Connecting to SSE: GET /api/v1/jobs/{job_id}")
    print("-" * 60)

    sse_url = f"{backend_url}/api/v1/jobs/{job_id}"
    events = []
    raw_lines = []

    try:
        with httpx.stream(
            "GET", sse_url, timeout=httpx.Timeout(120, connect=10),
        ) as response:
            print(f"  HTTP Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'MISSING')}")
            print(f"  Cache-Control: {response.headers.get('cache-control', 'MISSING')}")
            print(f"  X-Accel-Buffering: {response.headers.get('x-accel-buffering', 'MISSING')}")
            print()

            if response.status_code != 200:
                print(f"  FAIL: Expected 200, got {response.status_code}")
                body = response.read()
                print(f"  Body: {body.decode()[:500]}")
                sys.exit(1)

            current_event = "message"
            buffer = ""

            for chunk in response.iter_text():
                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    raw_lines.append(line)

                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        timestamp = time.strftime("%H:%M:%S")

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            data = data_str

                        event_info = {"event": current_event, "data": data}
                        events.append(event_info)

                        # Print with formatting
                        if current_event == "page_done":
                            page = data.get("page", "?")
                            total = data.get("total", "?")
                            content = str(data.get("content", ""))[:80]
                            elapsed = data.get("elapsed_ms", "?")
                            print(f"  [{timestamp}] PAGE_DONE {page}/{total} ({elapsed}ms)")
                            print(f"            content: {content}")

                            # Validate format
                            required = ["page", "total", "content", "elapsed_ms"]
                            missing = [k for k in required if k not in data]
                            if missing:
                                print(f"            WARNING: Missing fields: {missing}")
                        elif current_event == "job_complete":
                            print(f"  [{timestamp}] JOB_COMPLETE: {json.dumps(data, ensure_ascii=False)[:120]}")
                            # Validate
                            required = ["download_url", "total_pages"]
                            missing = [k for k in required if k not in data]
                            if missing:
                                print(f"            WARNING: Missing fields: {missing}")
                        elif current_event == "job_status":
                            print(f"  [{timestamp}] JOB_STATUS: {json.dumps(data)}")
                        elif current_event == "error":
                            print(f"  [{timestamp}] ERROR: {json.dumps(data, ensure_ascii=False)}")
                        else:
                            print(f"  [{timestamp}] {current_event}: {json.dumps(data, ensure_ascii=False)[:120]}")

                        if current_event in ("job_complete", "error"):
                            print()
                            break

                        current_event = "message"
                    elif line.startswith(":"):
                        # Comment (keepalive)
                        pass
                    elif line == "":
                        current_event = "message"
                else:
                    continue
                break

    except Exception as e:
        print(f"\n  SSE Error: {e}")

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    page_done_events = [e for e in events if e["event"] == "page_done"]
    complete_events = [e for e in events if e["event"] == "job_complete"]
    error_events = [e for e in events if e["event"] == "error"]

    print(f"  Total events: {len(events)}")
    print(f"  page_done: {len(page_done_events)}")
    print(f"  job_complete: {len(complete_events)}")
    print(f"  error: {len(error_events)}")

    has_content = any(
        isinstance(e["data"].get("content"), str) and len(e["data"].get("content", "")) > 0
        for e in page_done_events
    )

    if len(page_done_events) >= num_pages and has_content and len(complete_events) > 0:
        print("\n  PASS: Backend SSE is working correctly!")
        print("  If frontend doesn't show translations, the issue is in the frontend.")
        sys.exit(0)
    elif len(page_done_events) > 0 and not has_content:
        print("\n  PARTIAL: page_done events received but content is empty.")
        sys.exit(1)
    elif len(error_events) > 0:
        print(f"\n  FAIL: Error event received: {error_events[0]['data']}")
        sys.exit(1)
    elif len(events) == 0:
        print("\n  FAIL: No SSE events received at all!")
        print("  Possible causes:")
        print("  - SSE endpoint returned non-200")
        print("  - Content-Type not text/event-stream")
        print("  - Proxy buffering SSE")
        sys.exit(1)
    else:
        print(f"\n  PARTIAL: Only {len(page_done_events)} page_done events (expected {num_pages})")
        sys.exit(1)


if __name__ == "__main__":
    main()
