import { describe, it, expect, vi, beforeEach } from "vitest";
import { uploadPDF, getSSEUrl, getDownloadUrl, cancelJob } from "@/lib/api";

describe("API client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("getSSEUrl returns correct URL", () => {
    const url = getSSEUrl("job-123");
    expect(url).toContain("/api/v1/jobs/job-123");
  });

  it("getDownloadUrl returns correct URL", () => {
    const url = getDownloadUrl("job-456");
    expect(url).toContain("/api/v1/download/job-456");
  });

  it("uploadPDF sends FormData", async () => {
    const mockResponse = { job_id: "abc", status: "pending", filename: "test.pdf" };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const file = new File(["%PDF-"], "test.pdf", { type: "application/pdf" });
    const result = await uploadPDF(file);
    expect(result.job_id).toBe("abc");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/upload"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("uploadPDF throws on error response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ detail: "Invalid PDF" }),
    });

    const file = new File(["not-pdf"], "test.pdf", { type: "application/pdf" });
    await expect(uploadPDF(file)).rejects.toThrow("Invalid PDF");
  });

  it("cancelJob calls DELETE endpoint", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true });
    await cancelJob("job-123");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/jobs/job-123"),
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
