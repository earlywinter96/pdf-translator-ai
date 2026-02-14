"use client";

import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

export default function DownloadButton({ jobId }: { jobId: string }) {
  const [isDownloading, setIsDownloading] = useState(false);
  
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  
  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      console.log("🟢 Download started for jobId:", jobId);
      
      const downloadUrl = `${API_BASE}/api/download/${jobId}`;
      console.log("📥 Download URL:", downloadUrl);
      
      // Fetch the file
      const response = await fetch(downloadUrl);
      
      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }
      
      // Get the blob
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `translated_${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log("✅ Download completed successfully");
    } catch (error) {
      console.error("❌ Download failed:", error);
      alert("Download failed. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={isDownloading}
      className="px-6 py-3 rounded-lg text-white font-medium
        bg-gradient-to-r from-emerald-600 to-green-600
        hover:from-emerald-500 hover:to-green-500
        disabled:opacity-50 disabled:cursor-not-allowed
        transition shadow-lg flex items-center justify-center gap-2"
    >
      {isDownloading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          Downloading...
        </>
      ) : (
        <>
          <Download className="w-5 h-5" />
          Download Translation
        </>
      )}
    </button>
  );
}