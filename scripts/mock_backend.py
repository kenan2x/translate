#!/usr/bin/env python3
"""Mock backend that simulates the full upload + SSE flow.

Usage:
    python scripts/mock_backend.py          # port 8080
    python scripts/mock_backend.py --port 8080

Simulates:
- POST /api/v1/upload → returns job_id
- GET /api/v1/jobs/{job_id} → SSE stream with page_done events
- GET /health → ok
"""
import argparse
import asyncio
import json
import time
import uuid

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import threading


class MockBackend(BaseHTTPRequestHandler):
    # Store jobs in class variable
    jobs = {}

    def _send_cors_headers(self):
        # Echo back the Origin header (required when credentials: include)
        origin = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        if parsed.path.startswith("/api/v1/jobs/"):
            job_id = parsed.path.split("/")[-1]
            self._handle_sse(job_id)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/v1/upload":
            # Read and discard the uploaded file
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length:
                self.rfile.read(content_length)

            job_id = str(uuid.uuid4())[:8]
            MockBackend.jobs[job_id] = {
                "status": "processing",
                "total_pages": 3,
                "created_at": time.time(),
            }

            response = {
                "job_id": job_id,
                "status": "accepted",
                "filename": "test.pdf",
            }

            self.send_response(202)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return

        self.send_response(404)
        self.end_headers()

    def _handle_sse(self, job_id: str):
        """Simulate SSE stream with page_done events."""
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        total_pages = 3

        # Send connected event
        self._send_sse_event("job_status", {
            "job_id": job_id, "status": "connected",
        })
        self.wfile.flush()

        # Send processing status
        self._send_sse_event("job_status", {
            "job_id": job_id, "status": "processing",
        })
        self.wfile.flush()

        # Simulate page translations with delay
        for page in range(1, total_pages + 1):
            time.sleep(1.5)  # simulate translation time

            content = (
                f"Bu, sayfa {page}'nin Turkce cevirisidir. "
                f"Ornek metin burada gorunur. "
                f"API, HTTP, SSL gibi teknik terimler oldugu gibi kalir. "
                f"Ceviri gercek zamanli olarak gorunmektedir."
            )

            self._send_sse_event("page_done", {
                "page": page,
                "total": total_pages,
                "content": content,
                "elapsed_ms": 1200 + page * 100,
                "job_id": job_id,
            })
            self.wfile.flush()

        # Send job complete
        time.sleep(0.5)
        self._send_sse_event("job_complete", {
            "job_id": job_id,
            "download_url": f"/api/v1/download/{job_id}",
            "total_pages": total_pages,
        })
        self.wfile.flush()

    def _send_sse_event(self, event_type: str, data: dict):
        line = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(line.encode())

    def log_message(self, format, *args):
        print(f"[mock-backend] {args[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), MockBackend)
    print(f"Mock Backend running on http://0.0.0.0:{args.port}")
    print(f"  POST /api/v1/upload     → create job")
    print(f"  GET  /api/v1/jobs/{{id}} → SSE stream (3 pages, 1.5s each)")
    print(f"  GET  /health            → ok")
    print()
    print("To test with Playwright:")
    print(f"  FRONTEND_URL=http://localhost:3000 npx playwright test")
    server.serve_forever()
