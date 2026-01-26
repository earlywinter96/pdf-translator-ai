/**
 * Frontend API Client for PDF Translator
 * ----------------------------------------
 * Handles all communication with the FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

/**
 * Upload PDF for translation
 * 
 * @param file - PDF file to translate
 * @param language - Language code (gu, hi, mr)
 * @param direction - Translation direction (to_en, from_en)
 * @param mode - Translation mode (general, government)
 * @returns Promise with job_id and message
 */
export async function uploadPDF(
  file: File,
  language: string,
  direction: string,
  mode: string
): Promise<{ job_id: string; message: string }> {
  if (!API_BASE) {
    throw new Error("API base URL not configured. Set NEXT_PUBLIC_API_BASE_URL in .env.local");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);
  formData.append("direction", direction);
  formData.append("mode", mode);

  try {
    const response = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Failed to upload PDF");
    }

    return response.json();
  } catch (error) {
    console.error("Upload error:", error);
    throw error;
  }
}

/**
 * Get job status
 * 
 * @param jobId - Unique job identifier
 * @returns Promise with job status details
 */
export async function getJobStatus(jobId: string): Promise<{
  status: string;
  progress: number;
  message: string;
}> {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  try {
    const response = await fetch(
      `${API_BASE}/api/status/${jobId}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Failed to fetch job status");
    }

    return response.json();
  } catch (error) {
    console.error("Status fetch error:", error);
    throw error;
  }
}

/**
 * Download translated PDF
 * Uses proper blob handling instead of window.location.href
 * 
 * @param jobId - Unique job identifier
 * @returns Promise that resolves when download completes
 */
export async function downloadTranslatedPDF(jobId: string): Promise<void> {
  if (!API_BASE) {
    const error = "API base URL not configured. Check NEXT_PUBLIC_API_BASE_URL in .env.local";
    console.error("❌", error);
    alert(error);
    throw new Error(error);
  }

  const downloadUrl = `${API_BASE}/api/download/${jobId}`;
  
  try {
    console.log(`📥 Attempting to download from: ${downloadUrl}`);
    console.log(`   Job ID: ${jobId}`);
    
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/pdf',
      },
    });

    console.log(`📡 Response status: ${response.status} ${response.statusText}`);
    console.log(`📡 Response headers:`, Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const error = await response.text();
      console.error("❌ Download failed:", error);
      alert(`Download failed: ${error}`);
      throw new Error(error || "Failed to download PDF");
    }

    // Get the blob
    const blob = await response.blob();
    console.log(`✅ Received blob:`, {
      size: blob.size,
      type: blob.type,
    });
    
    if (blob.size === 0) {
      throw new Error("Received empty file");
    }
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `translated_${jobId}.pdf`;
    a.style.display = 'none';
    
    // Trigger download
    document.body.appendChild(a);
    console.log("🖱️ Triggering download...");
    a.click();
    
    // Cleanup
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      console.log("🧹 Cleanup complete");
    }, 100);
    
    console.log("✅ Download initiated successfully!");
  } catch (error) {
    console.error("❌ Download error:", error);
    if (error instanceof Error) {
      alert(`Download failed: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Download original PDF
 * 
 * @param jobId - Unique job identifier
 * @returns Promise that resolves when download completes
 */
export async function downloadOriginalPDF(jobId: string): Promise<void> {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  try {
    console.log(`📥 Downloading original PDF: ${jobId}`);
    
    const response = await fetch(`${API_BASE}/api/original/${jobId}`);

    if (!response.ok) {
      const error = await response.text();
      console.error("Original download failed:", error);
      throw new Error(error || "Failed to download original PDF");
    }

    const blob = await response.blob();
    console.log(`✅ Received original blob: ${blob.size} bytes`);
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `original_${jobId}.pdf`;
    
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }, 100);
    
    console.log("✅ Original download initiated");
  } catch (error) {
    console.error("Original download error:", error);
    throw error;
  }
}

/**
 * Health check endpoint
 * 
 * @returns Promise with health status
 */
export async function checkHealth(): Promise<{
  status: string;
  service: string;
}> {
  if (!API_BASE) {
    throw new Error("API base URL not configured");
  }

  try {
    const response = await fetch(`${API_BASE}/health`);

    if (!response.ok) {
      throw new Error("Health check failed");
    }

    return response.json();
  } catch (error) {
    console.error("Health check error:", error);
    throw error;
  }
}