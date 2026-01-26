// lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai.onrender.com";

export interface JobStatusResponse {
  status: string;
  progress: number;
  message: string;
}

export interface UploadResponse {
  job_id: string;
  message: string;
}

export async function uploadPDF(
  file: File,
  language: string,
  direction: string,
  mode: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  formData.append("direction", direction);
  formData.append("mode", mode);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ 
      detail: "Upload failed" 
    }));
    throw new Error(error.detail || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/api/status/${jobId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get status: ${response.statusText}`);
  }
  
  return response.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/download/${jobId}`;
}

export function getOriginalUrl(jobId: string): string {
  return `${API_BASE}/api/original/${jobId}`;
}

export function getPreviewUrls(jobId: string) {
  return {
    original: `${API_BASE}/api/preview/original/${jobId}`,
    translated: `${API_BASE}/api/preview/translated/${jobId}`,
  };
}