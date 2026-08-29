// lib/api.ts
/**
 * API Client Library
 * Sarvam AI translation and Gemini visualization backend
 */

// Production fallback for LipiTranslate. Override this locally with
// NEXT_PUBLIC_API_BASE=http://localhost:8000 in frontend/.env.local.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai-ggqe.onrender.com";

// ============================================================================
// LANGUAGE MAPPING (Updated for Sarvam AI)
// ============================================================================

export const SUPPORTED_LANGUAGES = {
  // Primary Indian Languages
  gujarati: { code: 'gu', name: 'Gujarati (ગુજરાતી)', flag: '🇮🇳' },
  hindi: { code: 'hi', name: 'Hindi (हिन्दी)', flag: '🇮🇳' },
  marathi: { code: 'mr', name: 'Marathi (मराठी)', flag: '🇮🇳' },
  english: { code: 'en', name: 'English', flag: '🇬🇧' },
  
  // Extended Indian Languages (via Sarvam AI)
  bengali: { code: 'bn', name: 'Bengali (বাংলা)', flag: '🇮🇳' },
  tamil: { code: 'ta', name: 'Tamil (தமிழ்)', flag: '🇮🇳' },
  telugu: { code: 'te', name: 'Telugu (తెలుగు)', flag: '🇮🇳' },
  kannada: { code: 'kn', name: 'Kannada (ಕನ್ನಡ)', flag: '🇮🇳' },
  malayalam: { code: 'ml', name: 'Malayalam (മലയാളം)', flag: '🇮🇳' },
  punjabi: { code: 'pa', name: 'Punjabi (ਪੰਜਾਬੀ)', flag: '🇮🇳' },
  odia: { code: 'od', name: 'Odia (ଓଡ଼ିଆ)', flag: '🇮🇳' },
  urdu: { code: 'ur', name: 'Urdu (اردو)', flag: '🇮🇳' },
};

export const PRIMARY_LANGUAGES = ['gujarati', 'hindi', 'marathi', 'english'];
export const EXTENDED_LANGUAGES = [
  'bengali', 'tamil', 'telugu', 'kannada', 
  'malayalam', 'punjabi', 'odia', 'urdu'
];

// ============================================================================
// PDF UTILITIES
// ============================================================================

export async function checkPdfPages(file: File) {
  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch(`${API_BASE}/api/check-pdf-pages`, {
    method: "POST",
    body: fd,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'PDF check failed' }));
    throw new Error(error.detail || 'PDF check failed');
  }
  
  return res.json();
}

// ============================================================================
// TRANSLATION API (Updated for Sarvam AI)
// ============================================================================

export interface TranslationRequest {
  file: File;
  source_language: string;  // e.g., "gujarati", "hindi"
  target_language: string;  // e.g., "english", "hindi"
  mode?: string;           // "general" | "formal" | "casual"
}

export async function uploadPDFForTranslation({
  file,
  source_language,
  target_language,
  mode = "general"
}: TranslationRequest) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("source_language", source_language);
  fd.append("target_language", target_language);
  fd.append("mode", mode);

  console.log('📤 Uploading PDF for translation:', {
    filename: file.name,
    size: `${(file.size / 1024 / 1024).toFixed(2)}MB`,
    source: source_language,
    target: target_language,
    translator: 'Sarvam AI'
  });

  const res = await fetch(`${API_BASE}/api/translate`, {
    method: "POST",
    body: fd,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Translation upload failed');
  }

  const result = await res.json();
  
  console.log('✅ Translation job created:', result.job_id);
  
  return result;
}

// Backward compatibility wrapper
export async function uploadPDF(
  file: File,
  language = "gu",
  direction = "to_en",
  mode = "general"
) {
  // Convert old format to new format
  const languageMap: Record<string, string> = {
    'gu': 'gujarati',
    'hi': 'hindi',
    'mr': 'marathi',
    'en': 'english',
  };
  
  const source_language = direction === "to_en" 
    ? (languageMap[language] || 'gujarati')
    : 'english';
    
  const target_language = direction === "to_en"
    ? 'english'
    : (languageMap[language] || 'gujarati');

  return uploadPDFForTranslation({
    file,
    source_language,
    target_language,
    mode
  });
}

// ============================================================================
// JOB STATUS
// ============================================================================

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API_BASE}/api/status/${jobId}`);
  
  if (!res.ok) {
    throw new Error('Status check failed');
  }
  
  const status = await res.json();
  
  // Add friendly messages
  if (status.status === 'processing' && !status.message) {
    if (status.progress < 30) {
      status.message = 'Extracting text from PDF...';
    } else if (status.progress < 70) {
      status.message = 'Translating with Sarvam AI...';
    } else {
      status.message = 'Generating translated PDF...';
    }
  }
  
  return status;
}

// ============================================================================
// VISUALIZATION API
// ============================================================================

export async function uploadPDFForVisualization(
  file: File,
  contentType?: string,
  outputFormat: "json" | "html" = "json"
) {
  const fd = new FormData();
  fd.append("file", file);
  if (contentType) fd.append("content_type", contentType);
  fd.append("output_format", outputFormat);

  console.log('📤 Uploading PDF for visualization:', {
    filename: file.name,
    size: `${(file.size / 1024 / 1024).toFixed(2)}MB`,
    engine: 'Google Gemini'
  });

  const res = await fetch(`${API_BASE}/api/visualize`, {
    method: "POST",
    body: fd,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Visualization failed' }));
    throw new Error(error.detail || 'Visualization upload failed');
  }
  
  return res.json();
}

export async function getVisualization(jobId: string) {
  const res = await fetch(`${API_BASE}/api/visualization/${jobId}`);
  
  if (!res.ok) {
    throw new Error('Visualization fetch failed');
  }
  
  return res.json();
}

// ============================================================================
// DOWNLOAD API
// ============================================================================

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/download/${jobId}`;
}

export async function downloadTranslatedPDF(jobId: string, filename?: string) {
  try {
    const response = await fetch(getDownloadUrl(jobId));
    
    if (!response.ok) {
      throw new Error('Download failed');
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `translated_${jobId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    console.log('✅ Download complete:', filename);
  } catch (error) {
    console.error('❌ Download failed:', error);
    throw error;
  }
}

// ============================================================================
// SYSTEM INFO
// ============================================================================

export async function getSystemInfo() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export function handleAPIError(error: unknown): APIError {
  if (error instanceof APIError) {
    return error;
  }
  
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = error.response as { data?: { detail?: string }; status?: number };
    return new APIError(
      response.data?.detail || 'API request failed',
      response.status,
      response.data
    );
  }
  
  return new APIError(
    error instanceof Error ? error.message : 'Unknown error occurred',
    undefined,
    error
  );
}
