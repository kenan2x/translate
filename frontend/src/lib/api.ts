const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export async function uploadPDF(file: File): Promise<{ job_id: string; status: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const resp = await fetch(`${API_BASE}/api/v1/upload`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || `Upload failed: ${resp.status}`);
  }

  return resp.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/jobs/${jobId}`, {
    method: "DELETE",
    credentials: "include",
  });
}

export function getSSEUrl(jobId: string): string {
  return `${API_BASE}/api/v1/jobs/${jobId}`;
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/v1/download/${jobId}`;
}
