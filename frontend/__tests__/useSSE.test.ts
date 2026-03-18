import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock EventSource before importing the hook
class MockEventSource {
  url: string;
  listeners: Record<string, Function[]> = {};
  readyState = 0;
  static readonly CLOSED = 2;

  constructor(url: string) {
    this.url = url;
  }

  addEventListener(event: string, handler: Function) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(handler);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  // Helper: simulate an event
  _emit(event: string, data: any) {
    const handlers = this.listeners[event] || [];
    handlers.forEach((h) => h({ data: JSON.stringify(data) }));
  }
}

describe("useSSE", () => {
  beforeEach(() => {
    vi.stubGlobal("EventSource", MockEventSource);
  });

  it("connects to SSE endpoint when jobId provided", async () => {
    const { renderHook } = await import("@testing-library/react");
    const { useSSE } = await import("@/hooks/useSSE");

    const { result } = renderHook(() => useSSE("job-123"));
    expect(result.current.progress.status).toBe("connected");
  });

  it("does not connect when jobId is null", async () => {
    const { renderHook } = await import("@testing-library/react");
    const { useSSE } = await import("@/hooks/useSSE");

    const { result } = renderHook(() => useSSE(null));
    expect(result.current.progress.pages).toEqual([]);
  });
});
