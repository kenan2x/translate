"use client";

interface JobProgressProps {
  status: string;
  currentPage: number;
  totalPages: number;
  error?: string;
}

export function JobProgress({ status, currentPage, totalPages, error }: JobProgressProps) {
  const percent = totalPages > 0 ? Math.round((currentPage / totalPages) * 100) : 0;

  const statusText: Record<string, string> = {
    connected: "Baglanti kuruldu",
    processing: `Ceviri yapiliyor... Sayfa ${currentPage}/${totalPages}`,
    completed: "Ceviri tamamlandi!",
    failed: error || "Ceviri basarisiz",
    cancelled: "Ceviri iptal edildi",
  };

  const statusColor: Record<string, string> = {
    connected: "#3b82f6",
    processing: "#f59e0b",
    completed: "#10b981",
    failed: "#ef4444",
    cancelled: "#6b7280",
  };

  return (
    <div
      data-testid="job-progress"
      style={{
        padding: "16px",
        backgroundColor: "#f9fafb",
        borderRadius: "8px",
        border: "1px solid #e5e7eb",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "8px",
        }}
      >
        <span
          style={{
            fontSize: "14px",
            fontWeight: 500,
            color: statusColor[status] || "#374151",
          }}
        >
          {statusText[status] || status}
        </span>
        {status === "processing" && (
          <span style={{ fontSize: "14px", color: "#6b7280" }}>{percent}%</span>
        )}
      </div>

      {/* Progress bar */}
      {(status === "processing" || status === "completed") && (
        <div
          style={{
            width: "100%",
            height: "6px",
            backgroundColor: "#e5e7eb",
            borderRadius: "3px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${status === "completed" ? 100 : percent}%`,
              height: "100%",
              backgroundColor: status === "completed" ? "#10b981" : "#3b82f6",
              borderRadius: "3px",
              transition: "width 0.3s ease",
            }}
          />
        </div>
      )}
    </div>
  );
}
