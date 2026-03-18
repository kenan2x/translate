"use client";

import { useState } from "react";

type AdminTab = "dashboard" | "users" | "capacity" | "reports" | "audit" | "glossary" | "settings";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("dashboard");

  const tabs: { key: AdminTab; label: string }[] = [
    { key: "dashboard", label: "Dashboard" },
    { key: "users", label: "Kullanicilar" },
    { key: "capacity", label: "Kapasite" },
    { key: "reports", label: "Raporlar" },
    { key: "audit", label: "Audit Log" },
    { key: "glossary", label: "Glossary" },
    { key: "settings", label: "Ayarlar" },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f3f4f6" }}>
      {/* Header */}
      <header
        style={{
          backgroundColor: "#1f2937",
          color: "#ffffff",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700 }}>Admin Panel</h1>
        <a href="/" style={{ color: "#9ca3af", fontSize: "14px" }}>
          Ana Sayfaya Don
        </a>
      </header>

      {/* Tabs */}
      <nav
        style={{
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e5e7eb",
          padding: "0 24px",
          display: "flex",
          gap: "0",
          overflowX: "auto",
        }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: "12px 20px",
              fontSize: "14px",
              fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? "#3b82f6" : "#6b7280",
              borderBottom: activeTab === tab.key ? "2px solid #3b82f6" : "2px solid transparent",
              backgroundColor: "transparent",
              border: "none",
              borderBottomWidth: "2px",
              borderBottomStyle: "solid",
              borderBottomColor: activeTab === tab.key ? "#3b82f6" : "transparent",
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "24px" }}>
        {activeTab === "dashboard" && <DashboardPanel />}
        {activeTab === "users" && <UsersPanel />}
        {activeTab === "capacity" && <CapacityPanel />}
        {activeTab === "reports" && <ReportsPanel />}
        {activeTab === "audit" && <AuditPanel />}
        {activeTab === "glossary" && <GlossaryPanel />}
        {activeTab === "settings" && <SettingsPanel />}
      </main>
    </div>
  );
}

function DashboardPanel() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
      <StatCard label="Aktif Isler" value="-" color="#3b82f6" />
      <StatCard label="Kuyruk Derinligi" value="-" color="#f59e0b" />
      <StatCard label="Bugun Cevrilen Sayfa" value="-" color="#10b981" />
      <StatCard label="Aktif Kullanicilar" value="-" color="#8b5cf6" />
      <StatCard label="Hata Sayisi" value="-" color="#ef4444" />
      <StatCard label="GPU VRAM" value="-" color="#06b6d4" />
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      style={{
        padding: "20px",
        backgroundColor: "#ffffff",
        borderRadius: "8px",
        border: "1px solid #e5e7eb",
        borderLeft: `4px solid ${color}`,
      }}
    >
      <p style={{ fontSize: "12px", color: "#6b7280", marginBottom: "8px" }}>{label}</p>
      <p style={{ fontSize: "28px", fontWeight: 700, color: "#111827" }}>{value}</p>
    </div>
  );
}

function UsersPanel() {
  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Kullanici Yonetimi</h2>
      <p style={{ color: "#6b7280" }}>Kullanici listesi ve tier yonetimi burada gorunecek.</p>
    </div>
  );
}

function CapacityPanel() {
  const [result, setResult] = useState<any>(null);

  const calculate = async () => {
    const resp = await fetch(`${API_BASE}/api/v1/admin/capacity/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        total_vram_gb: 286,
        model_weight_vram_gb: 122,
        context_window_tokens: 32768,
        kv_cache_type: "fp8",
        kv_cache_vram_percent: 0.4,
        avg_page_tokens: 400,
        avg_translation_tokens: 600,
        vllm_overhead_factor: 0.7,
        avg_page_seconds: 4.0,
      }),
    });
    if (resp.ok) setResult(await resp.json());
  };

  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Model Kapasite Hesaplayici</h2>
      <button
        onClick={calculate}
        style={{
          padding: "8px 16px",
          backgroundColor: "#3b82f6",
          color: "#fff",
          borderRadius: "6px",
          border: "none",
          cursor: "pointer",
          marginBottom: "16px",
        }}
      >
        Hesapla
      </button>
      {result && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>Kullanilabilir VRAM: <strong>{result.available_vram_gb} GB</strong></div>
          <div>KV Cache VRAM: <strong>{result.kv_cache_vram_gb} GB</strong></div>
          <div>Teorik Eszamanli: <strong>{result.theoretical_concurrent}</strong></div>
          <div>Guvenli Eszamanli: <strong>{result.safe_concurrent}</strong></div>
          <div>Saatlik Sayfa: <strong>{result.pages_per_hour}</strong></div>
          <div>Gunluk Sayfa: <strong>{result.pages_per_day}</strong></div>
        </div>
      )}
    </div>
  );
}

function ReportsPanel() {
  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Raporlar</h2>
      <div style={{ display: "flex", gap: "12px" }}>
        <a
          href={`${API_BASE}/api/v1/admin/reports/export/csv`}
          style={{
            padding: "8px 16px",
            backgroundColor: "#10b981",
            color: "#fff",
            borderRadius: "6px",
            fontSize: "14px",
          }}
        >
          CSV Export
        </a>
      </div>
    </div>
  );
}

function AuditPanel() {
  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Audit Log</h2>
      <p style={{ color: "#6b7280" }}>Tum sistem olaylari burada gorunecek. 90 gun saklama suresi.</p>
      <a
        href={`${API_BASE}/api/v1/admin/audit/export/csv`}
        style={{
          display: "inline-block",
          marginTop: "12px",
          padding: "8px 16px",
          backgroundColor: "#10b981",
          color: "#fff",
          borderRadius: "6px",
          fontSize: "14px",
        }}
      >
        CSV Export
      </a>
    </div>
  );
}

function GlossaryPanel() {
  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Glossary Yonetimi</h2>
      <p style={{ color: "#6b7280" }}>Teknik terimler burada yonetilecek. CSV import/export destegi.</p>
    </div>
  );
}

function SettingsPanel() {
  return (
    <div style={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>Sistem Ayarlari</h2>
      <p style={{ color: "#6b7280" }}>Kota konfigurasyonu, worker sayisi, TTL, bakim modu ayarlari.</p>
    </div>
  );
}
