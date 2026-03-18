"use client";

import { useState, useEffect } from "react";
import { getDownloadUrl } from "@/lib/api";

interface HistoryItem {
  id: string;
  filename: string;
  status: string;
  page_count: number;
  translated_pages: number;
  created_at: string;
  completed_at: string | null;
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const resp = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/history`,
          { credentials: "include" }
        );
        if (resp.ok) {
          const data = await resp.json();
          setItems(data.items || []);
        }
      } catch {
        // silently fail
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const statusLabels: Record<string, string> = {
    completed: "Tamamlandi",
    processing: "Isleniyor",
    failed: "Basarisiz",
    pending: "Bekliyor",
    cancelled: "Iptal",
  };

  const statusColors: Record<string, string> = {
    completed: "#10b981",
    processing: "#f59e0b",
    failed: "#ef4444",
    pending: "#6b7280",
    cancelled: "#9ca3af",
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f3f4f6" }}>
      <header
        style={{
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e5e7eb",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700 }}>Ceviri Gecmisi</h1>
        <a href="/" style={{ color: "#3b82f6", fontSize: "14px" }}>
          Ana Sayfaya Don
        </a>
      </header>

      <main style={{ maxWidth: "900px", margin: "0 auto", padding: "24px" }}>
        {loading ? (
          <p style={{ textAlign: "center", color: "#6b7280", padding: "48px" }}>
            Yukleniyor...
          </p>
        ) : items.length === 0 ? (
          <p style={{ textAlign: "center", color: "#6b7280", padding: "48px" }}>
            Henuz ceviri gecmisiniz yok.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {items.map((item) => (
              <div
                key={item.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "16px",
                  backgroundColor: "#ffffff",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <div>
                  <p style={{ fontWeight: 500, color: "#111827" }}>{item.filename}</p>
                  <p style={{ fontSize: "12px", color: "#6b7280" }}>
                    {item.page_count} sayfa | {new Date(item.created_at).toLocaleString("tr-TR")}
                  </p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span
                    style={{
                      fontSize: "12px",
                      padding: "4px 8px",
                      borderRadius: "12px",
                      backgroundColor: `${statusColors[item.status]}20`,
                      color: statusColors[item.status],
                      fontWeight: 500,
                    }}
                  >
                    {statusLabels[item.status] || item.status}
                  </span>
                  {item.status === "completed" && (
                    <a
                      href={getDownloadUrl(item.id)}
                      style={{
                        padding: "6px 12px",
                        backgroundColor: "#3b82f6",
                        color: "#ffffff",
                        borderRadius: "4px",
                        fontSize: "12px",
                        fontWeight: 500,
                      }}
                    >
                      Indir
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
