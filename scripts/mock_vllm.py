"""Mock vLLM server — OpenAI-compatible chat API.

Usage:
    python scripts/mock_vllm.py          # port 8099
    python scripts/mock_vllm.py --port 8099

Responds to POST /v1/chat/completions with a fake Turkish translation.
"""
import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/chat/completions":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            # Extract user message
            messages = body.get("messages", [])
            user_msg = ""
            for m in messages:
                if m.get("role") == "user":
                    user_msg = m.get("content", "")

            # Simulate translation delay (0.5s per page)
            time.sleep(0.5)

            translated = f"[TR] {user_msg[:200]}" if user_msg else "[TR] (bos sayfa)"

            response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", "mock-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": translated},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/v1/models":
            response = {"data": [{"id": "mock-model", "object": "model"}]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/v1/models":
            response = {"data": [{"id": "mock-model", "object": "model"}]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[mock-vllm] {args[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), MockHandler)
    print(f"Mock vLLM running on http://0.0.0.0:{args.port}")
    print(f"  POST /v1/chat/completions — fake translation")
    print(f"  GET  /v1/models — model list")
    server.serve_forever()
