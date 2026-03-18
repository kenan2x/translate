"use client";

import { useEffect, useRef, useState } from "react";

interface PDFViewerProps {
  url: string | null;
  currentPage: number;
  onPageChange: (page: number) => void;
  totalPages?: number;
}

export function PDFViewer({ url, currentPage, onPageChange, totalPages = 0 }: PDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!url || typeof window === "undefined") return;

    // PDF.js rendering will be initialized here
    // For now, we use an iframe as a simple PDF viewer
    setLoading(true);
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, [url, currentPage]);

  if (!url) {
    return (
      <div
        data-testid="pdf-viewer"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          minHeight: "400px",
          backgroundColor: "#f3f4f6",
          borderRadius: "8px",
          color: "#9ca3af",
          fontSize: "16px",
        }}
      >
        PDF yuklendikten sonra burada gorunecek
      </div>
    );
  }

  return (
    <div data-testid="pdf-viewer" style={{ height: "100%", position: "relative" }}>
      {/* Page navigation */}
      {totalPages > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            padding: "8px",
            backgroundColor: "#f9fafb",
            borderBottom: "1px solid #e5e7eb",
          }}
        >
          <button
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage <= 1}
            style={{
              padding: "4px 12px",
              borderRadius: "4px",
              border: "1px solid #d1d5db",
              cursor: currentPage <= 1 ? "not-allowed" : "pointer",
              opacity: currentPage <= 1 ? 0.5 : 1,
            }}
          >
            Onceki
          </button>
          <span style={{ fontSize: "14px", color: "#374151" }}>
            Sayfa {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage >= totalPages}
            style={{
              padding: "4px 12px",
              borderRadius: "4px",
              border: "1px solid #d1d5db",
              cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
              opacity: currentPage >= totalPages ? 0.5 : 1,
            }}
          >
            Sonraki
          </button>
        </div>
      )}

      {/* PDF content */}
      <iframe
        ref={containerRef as any}
        src={`${url}#page=${currentPage}`}
        style={{
          width: "100%",
          height: "calc(100% - 50px)",
          border: "none",
          minHeight: "500px",
        }}
        title="PDF Viewer"
      />

      {loading && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            backgroundColor: "rgba(255,255,255,0.9)",
            padding: "16px 24px",
            borderRadius: "8px",
          }}
        >
          Yukleniyor...
        </div>
      )}
    </div>
  );
}
