"use client";

import { useState, useCallback } from "react";
import { UploadZone } from "@/components/UploadZone";
import { PDFViewer } from "@/components/PDFViewer";
import { TranslationPanel } from "@/components/TranslationPanel";
import { JobProgress } from "@/components/JobProgress";
import { useSSE } from "@/hooks/useSSE";
import { uploadPDF, getDownloadUrl } from "@/lib/api";

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { progress } = useSSE(jobId);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setUploadError(null);

    // Create local URL for PDF viewer
    const localUrl = URL.createObjectURL(file);
    setPdfUrl(localUrl);

    try {
      const result = await uploadPDF(file);
      setJobId(result.job_id);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
      setPdfUrl(null);
    } finally {
      setUploading(false);
    }
  }, []);

  const isTranslating = jobId !== null;
  const isCompleted = progress.status === "completed";

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f3f4f6" }}>
      {/* Header */}
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
        <h1 style={{ fontSize: "20px", fontWeight: 700, color: "#111827" }}>
          Takasbank PDF Translator
        </h1>
        {isCompleted && (
          <a
            href={getDownloadUrl(jobId!)}
            style={{
              padding: "8px 20px",
              backgroundColor: "#10b981",
              color: "#ffffff",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Ceviriyi Indir
          </a>
        )}
      </header>

      <main style={{ maxWidth: "1400px", margin: "0 auto", padding: "24px" }}>
        {/* Upload zone (only show if no job) */}
        {!isTranslating && (
          <div style={{ maxWidth: "600px", margin: "40px auto" }}>
            <UploadZone onUpload={handleUpload} disabled={uploading} />
            {uploadError && (
              <p style={{ color: "#ef4444", marginTop: "12px", textAlign: "center" }}>
                {uploadError}
              </p>
            )}
          </div>
        )}

        {/* Progress bar */}
        {isTranslating && (
          <div style={{ marginBottom: "16px" }}>
            <JobProgress
              status={progress.status}
              currentPage={progress.currentPage}
              totalPages={progress.totalPages}
              error={progress.error}
            />
          </div>
        )}

        {/* Split view */}
        {isTranslating && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
              height: "calc(100vh - 200px)",
            }}
          >
            {/* Left: Original PDF */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#f9fafb",
                  borderBottom: "1px solid #e5e7eb",
                  fontWeight: 600,
                  fontSize: "14px",
                  color: "#374151",
                }}
              >
                Orijinal PDF
              </div>
              <PDFViewer
                url={pdfUrl}
                currentPage={currentPage}
                onPageChange={setCurrentPage}
                totalPages={progress.totalPages}
              />
            </div>

            {/* Right: Translation */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#f9fafb",
                  borderBottom: "1px solid #e5e7eb",
                  fontWeight: 600,
                  fontSize: "14px",
                  color: "#374151",
                }}
              >
                Turkce Ceviri
              </div>
              <TranslationPanel
                pages={progress.pages}
                currentPage={currentPage}
                status={progress.status}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
