"use client";

import { useEffect, useRef } from "react";
import type { TranslatedPage } from "@/hooks/useSSE";

interface TranslationPanelProps {
  pages: TranslatedPage[];
  currentPage: number;
  status?: string;
}

export function TranslationPanel({ pages, currentPage, status }: TranslationPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest page
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [pages.length]);

  if (pages.length === 0) {
    return (
      <div
        data-testid="translation-panel"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          minHeight: "400px",
          backgroundColor: "#f9fafb",
          borderRadius: "8px",
          padding: "24px",
        }}
      >
        {status === "processing" ? (
          <>
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>
              {"\u23F3"}
            </div>
            <p style={{ color: "#6b7280", fontSize: "16px" }}>
              Ceviri baslatildi, sayfalar gelmeye baslayacak...
            </p>
          </>
        ) : (
          <>
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>
              {"\u{1F4DD}"}
            </div>
            <p style={{ color: "#9ca3af", fontSize: "16px" }}>
              Turkce ceviri burada gorunecek
            </p>
          </>
        )}
      </div>
    );
  }

  // Find the page matching currentPage, or show all
  const pageToShow = pages.find((p) => p.page === currentPage) || pages[pages.length - 1];

  return (
    <div
      ref={scrollRef}
      data-testid="translation-panel"
      style={{
        height: "100%",
        overflow: "auto",
        padding: "24px",
        backgroundColor: "#ffffff",
        borderRadius: "8px",
        border: "1px solid #e5e7eb",
        lineHeight: "1.8",
        fontSize: "15px",
        color: "#1f2937",
      }}
    >
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
          paddingBottom: "12px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <span style={{ fontWeight: 600, color: "#374151" }}>
          Sayfa {pageToShow.page}
        </span>
        {pageToShow.elapsed_ms && (
          <span style={{ fontSize: "12px", color: "#9ca3af" }}>
            {(pageToShow.elapsed_ms / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      {/* Translation content */}
      <div style={{ whiteSpace: "pre-wrap" }}>{pageToShow.content}</div>

      {/* Page selector */}
      {pages.length > 1 && (
        <div
          style={{
            display: "flex",
            gap: "6px",
            flexWrap: "wrap",
            marginTop: "24px",
            paddingTop: "16px",
            borderTop: "1px solid #e5e7eb",
          }}
        >
          {pages.map((p) => (
            <span
              key={p.page}
              style={{
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "12px",
                backgroundColor: p.page === currentPage ? "#3b82f6" : "#f3f4f6",
                color: p.page === currentPage ? "#ffffff" : "#6b7280",
              }}
            >
              {p.page}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
