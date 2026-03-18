"use client";

interface QuotaBarProps {
  dailyUsed: number;
  dailyLimit: number | null;
  monthlyUsed: number;
  monthlyLimit: number | null;
  tier: string;
}

export function QuotaBar({ dailyUsed, dailyLimit, monthlyUsed, monthlyLimit, tier }: QuotaBarProps) {
  const tierLabels: Record<string, string> = {
    standard: "Standart",
    power_user: "Power User",
    vip: "VIP",
    admin: "Admin",
  };

  const dailyPercent = dailyLimit ? Math.min((dailyUsed / dailyLimit) * 100, 100) : 0;
  const monthlyPercent = monthlyLimit ? Math.min((monthlyUsed / monthlyLimit) * 100, 100) : 0;

  const barColor = (percent: number) => {
    if (percent >= 90) return "#ef4444";
    if (percent >= 70) return "#f59e0b";
    return "#10b981";
  };

  return (
    <div
      data-testid="quota-bar"
      style={{
        padding: "16px",
        backgroundColor: "#ffffff",
        borderRadius: "8px",
        border: "1px solid #e5e7eb",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
        <span style={{ fontSize: "14px", fontWeight: 600, color: "#374151" }}>
          Kota Durumu
        </span>
        <span
          style={{
            fontSize: "12px",
            padding: "2px 8px",
            borderRadius: "12px",
            backgroundColor: "#f3f4f6",
            color: "#6b7280",
          }}
        >
          {tierLabels[tier] || tier}
        </span>
      </div>

      {/* Daily quota */}
      {dailyLimit !== null ? (
        <div style={{ marginBottom: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <span style={{ fontSize: "12px", color: "#6b7280" }}>Gunluk</span>
            <span style={{ fontSize: "12px", color: "#374151", fontWeight: 500 }}>
              {dailyUsed} / {dailyLimit} sayfa
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: "6px",
              backgroundColor: "#e5e7eb",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                width: `${dailyPercent}%`,
                height: "100%",
                backgroundColor: barColor(dailyPercent),
                borderRadius: "3px",
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      ) : (
        <p style={{ fontSize: "12px", color: "#10b981", marginBottom: "12px" }}>
          Gunluk kota: Sinirsiz
        </p>
      )}

      {/* Monthly quota */}
      {monthlyLimit !== null ? (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <span style={{ fontSize: "12px", color: "#6b7280" }}>Aylik</span>
            <span style={{ fontSize: "12px", color: "#374151", fontWeight: 500 }}>
              {monthlyUsed} / {monthlyLimit} sayfa
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: "6px",
              backgroundColor: "#e5e7eb",
              borderRadius: "3px",
            }}
          >
            <div
              style={{
                width: `${monthlyPercent}%`,
                height: "100%",
                backgroundColor: barColor(monthlyPercent),
                borderRadius: "3px",
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      ) : (
        <p style={{ fontSize: "12px", color: "#10b981" }}>Aylik kota: Sinirsiz</p>
      )}
    </div>
  );
}
