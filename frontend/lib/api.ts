/ lib/api.ts

// Get API base URL from environment variable
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://pdf-translator-ai.onrender.com';

// Debug: Log the API base on load
if (typeof window !== 'undefined') {
  console.log('🔗 API_BASE:', API_BASE);
  console.log('🌍 Environment:', process.env.NODE_ENV);
}

export interface JobStatusResponse {
  status: string;
  progress: number;
  message: string;
}

export interface UploadResponse {
  job_id: string;
  message: string;
}

/**
 * Upload PDF for translation
 */
export async function uploadPDF(
  file: File,
  language: string,
  direction: string,
  mode: string
): Promise<UploadResponse> {
  console.log('📤 Starting upload...');
  console.log('   File:', file.name, file.size, 'bytes');
  console.log('   Language:', language);
  console.log('   Direction:', direction);
  console.log('   Mode:', mode);
  console.log('   Endpoint:', `${API_BASE}/api/upload`);

  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);
  formData.append('direction', direction);
  formData.append('mode', mode);

  try {
    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    console.log('📥 Response received:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      
      let error;
      try {
        error = JSON.parse(errorText);
      } catch {
        error = { detail: errorText || 'Upload failed' };
      }
      
      throw new Error(error.detail || `Upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Upload successful:', data);
    return data;
    
  } catch (error) {
    console.error('❌ Upload error:', error);
    throw error;
  }
}

/**
 * Get job status
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/api/status/${jobId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get status: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get download URL for translated PDF
 */
export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/download/${jobId}`;
}

/**
 * Get download URL for original PDF
 */
export function getOriginalUrl(jobId: string): string {
  return `${API_BASE}/api/original/${jobId}`;
}

/**
 * Get preview URLs
 */
export function getPreviewUrls(jobId: string) {
  return {
    original: `${API_BASE}/api/preview/original/${jobId}`,
    translated: `${API_BASE}/api/preview/translated/${jobId}`,
  };
}