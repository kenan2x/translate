"use client";

interface QueuePositionProps {
  position: number;
  status: string;
}

export function QueuePosition({ position, status }: QueuePositionProps) {
  if (status !== "connected" && status !== "pending") return null;
  if (position <= 0) return null;

  return (
    <div
      data-testid="queue-position"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "16px",
        backgroundColor: "#fef3c7",
        borderRadius: "8px",
        border: "1px solid #fbbf24",
      }}
    >
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: "50%",
          backgroundColor: "#f59e0b",
          color: "#ffffff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 700,
          fontSize: "18px",
        }}
      >
        {position}
      </div>
      <div>
        <p style={{ fontWeight: 600, color: "#92400e", fontSize: "14px" }}>
          Kuyrukta {position}. siradasiniz
        </p>
        <p style={{ fontSize: "12px", color: "#b45309" }}>
          Siraniz gelince ceviri otomatik baslar
        </p>
      </div>
    </div>
  );
}
