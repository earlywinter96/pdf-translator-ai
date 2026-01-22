const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

/**
 * Upload PDF for translation
 */
export async function uploadPDF(
  file: File,
  language: string,
  direction: string,
  mode: string
): Promise<{ job_id: string; message: string }> {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  formData.append("direction", direction);
  formData.append("mode", mode);

  const response = await fetch(`${API_BASE}/api/translate`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to upload PDF");
  }

  return response.json();
}

/**
 * Get job status
 */
export async function getJobStatus(jobId: string): Promise<{
  status: string;
  progress: number;
  message: string;
}> {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  const response = await fetch(
    `${API_BASE}/api/status/${jobId}`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }

  return response.json();
}

/**
 * Download translated PDF
 */
export function downloadTranslatedPDF(jobId: string) {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  window.location.href = `${API_BASE}/api/download/${jobId}`;
}
