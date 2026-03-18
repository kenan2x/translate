"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getSSEUrl } from "@/lib/api";

export interface TranslatedPage {
  page: number;
  content: string;
  elapsed_ms?: number;
}

export interface JobProgress {
  status: "connected" | "processing" | "completed" | "failed" | "cancelled";
  currentPage: number;
  totalPages: number;
  pages: TranslatedPage[];
  error?: string;
  downloadUrl?: string;
}

export function useSSE(jobId: string | null) {
  const [progress, setProgress] = useState<JobProgress>({
    status: "connected",
    currentPage: 0,
    totalPages: 0,
    pages: [],
  });
  const eventSourceRef = useRef<EventSource | null>(null);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    const es = new EventSource(getSSEUrl(jobId));
    eventSourceRef.current = es;

    es.addEventListener("job_status", (e) => {
      const data = JSON.parse(e.data);
      setProgress((prev) => ({
        ...prev,
        status: data.status,
      }));
    });

    es.addEventListener("page_start", (e) => {
      const data = JSON.parse(e.data);
      setProgress((prev) => ({
        ...prev,
        currentPage: data.page,
        totalPages: data.total || prev.totalPages,
      }));
    });

    es.addEventListener("page_done", (e) => {
      const data = JSON.parse(e.data);
      setProgress((prev) => ({
        ...prev,
        currentPage: data.page,
        totalPages: data.total || prev.totalPages,
        pages: [
          ...prev.pages,
          {
            page: data.page,
            content: data.content || "",
            elapsed_ms: data.elapsed_ms,
          },
        ],
      }));
    });

    es.addEventListener("job_complete", (e) => {
      const data = JSON.parse(e.data);
      setProgress((prev) => ({
        ...prev,
        status: "completed",
        downloadUrl: data.download_url,
        totalPages: data.total_pages || prev.totalPages,
      }));
      es.close();
    });

    es.addEventListener("error", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setProgress((prev) => ({
          ...prev,
          status: "failed",
          error: data.message || "Translation failed",
        }));
      } catch {
        setProgress((prev) => ({
          ...prev,
          status: "failed",
          error: "Connection lost",
        }));
      }
      es.close();
    });

    es.onerror = () => {
      // EventSource auto-reconnects, but if it's closed, update status
      if (es.readyState === EventSource.CLOSED) {
        setProgress((prev) => {
          if (prev.status === "completed" || prev.status === "failed") return prev;
          return { ...prev, status: "failed", error: "Connection lost" };
        });
      }
    };

    return () => {
      es.close();
    };
  }, [jobId]);

  return { progress, disconnect };
}
