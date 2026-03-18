"use client";

import { useState, useCallback, useRef } from "react";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onUpload, disabled = false }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndUpload = useCallback(
    (file: File) => {
      setError(null);

      if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
        setError("Sadece PDF dosyalari yuklenebilir.");
        return;
      }

      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) validateAndUpload(file);
    },
    [disabled, validateAndUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndUpload(file);
      // Reset input so same file can be selected again
      if (inputRef.current) inputRef.current.value = "";
    },
    [validateAndUpload]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      style={{
        border: `2px dashed ${isDragging ? "#3b82f6" : "#d1d5db"}`,
        borderRadius: "12px",
        padding: "48px 24px",
        textAlign: "center",
        cursor: disabled ? "not-allowed" : "pointer",
        backgroundColor: isDragging ? "#eff6ff" : disabled ? "#f9fafb" : "#ffffff",
        transition: "all 0.2s ease",
        opacity: disabled ? 0.6 : 1,
      }}
      data-testid="upload-zone"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleChange}
        style={{ display: "none" }}
        data-testid="file-input"
        disabled={disabled}
      />

      <div style={{ fontSize: "48px", marginBottom: "16px" }}>
        {isDragging ? "\u{1F4E5}" : "\u{1F4C4}"}
      </div>

      <p style={{ fontSize: "18px", fontWeight: 600, color: "#374151", marginBottom: "8px" }}>
        {isDragging ? "Dosyayi birakin" : "PDF dosyanizi surukleyin veya tiklayin"}
      </p>

      <p style={{ fontSize: "14px", color: "#6b7280" }}>Maksimum dosya boyutu: 50 MB</p>

      {error && (
        <p
          style={{
            color: "#ef4444",
            marginTop: "12px",
            fontSize: "14px",
            fontWeight: 500,
          }}
          data-testid="upload-error"
        >
          {error}
        </p>
      )}
    </div>
  );
}
