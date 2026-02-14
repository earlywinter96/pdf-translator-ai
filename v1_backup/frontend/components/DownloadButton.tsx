"use client";

import { Download } from "lucide-react";

export default function DownloadButton({ jobId }: { jobId: string }) {
  
  const handleDownload = async () => {
    try {
      console.log("🟢 Download started for jobId:", jobId);
      
      // FIX: Use correct environment variable name
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://pdf-translator-ai.onrender.com';
      const downloadUrl = `${API_BASE}/api/download/${jobId}`;
      
      console.log("📥 Download URL:", downloadUrl);
      
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `translated_${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log("✅ Download triggered successfully");
    } catch (error) {
      console.error("❌ Download failed:", error);
      alert("Download failed. Please try again.");
    }
  };

  return (
    <button
      onClick={handleDownload}
      className="px-6 py-3 rounded-lg text-white font-medium
        bg-gradient-to-r from-emerald-600 to-green-600
        hover:from-emerald-500 hover:to-green-500
        transition shadow-lg flex items-center justify-center gap-2"
    >
      <Download className="w-5 h-5" />
      Download Translation
    </button>
  );
}