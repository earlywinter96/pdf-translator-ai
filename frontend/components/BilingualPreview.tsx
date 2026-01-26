"use client";

import { useState } from "react";
import { FileText } from "lucide-react";

interface Props {
  jobId: string;
}

export default function BilingualPreview({ jobId }: Props) {
  const [activeTab, setActiveTab] = useState<"side-by-side" | "original" | "translated">("side-by-side");

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  
  // Use preview endpoints instead of download endpoints
  const originalUrl = `${API_BASE}/api/preview/original/${jobId}`;
  const translatedUrl = `${API_BASE}/api/preview/translated/${jobId}`;

  return (
    <div className="space-y-4">
      
      {/* View Toggle Tabs */}
      <div className="flex justify-center gap-2 flex-wrap">
        <button
          onClick={() => setActiveTab("side-by-side")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "side-by-side"
              ? "bg-cyan-600 text-white"
              : "bg-white/5 text-gray-400 hover:bg-white/10"
          }`}
        >
          Side-by-Side
        </button>
        <button
          onClick={() => setActiveTab("original")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "original"
              ? "bg-cyan-600 text-white"
              : "bg-white/5 text-gray-400 hover:bg-white/10"
          }`}
        >
          Original Only
        </button>
        <button
          onClick={() => setActiveTab("translated")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "translated"
              ? "bg-cyan-600 text-white"
              : "bg-white/5 text-gray-400 hover:bg-white/10"
          }`}
        >
          Translated Only
        </button>
      </div>

      {/* Preview Container */}
      <div className={`grid gap-4 ${
        activeTab === "side-by-side" ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1 max-w-4xl mx-auto"
      }`}>
        
        {/* Original PDF */}
        {(activeTab === "side-by-side" || activeTab === "original") && (
          <div className="rounded-xl overflow-hidden border border-white/10 bg-gray-900 shadow-xl">
            
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-300">
                  Original Document
                </span>
              </div>
            </div>

            {/* PDF Viewer */}
            <div className="relative bg-gray-800" style={{ height: "600px" }}>
              <iframe
                src={originalUrl}
                className="w-full h-full border-0"
                title="Original PDF"
              />
            </div>
          </div>
        )}

        {/* Translated PDF */}
        {(activeTab === "side-by-side" || activeTab === "translated") && (
          <div className="rounded-xl overflow-hidden border border-white/10 bg-gray-900 shadow-xl">
            
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-gray-300">
                  Translated Document
                </span>
                <span className="px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
                  English
                </span>
              </div>
            </div>

            {/* PDF Viewer */}
            <div className="relative bg-gray-800" style={{ height: "600px" }}>
              <iframe
                src={translatedUrl}
                className="w-full h-full border-0"
                title="Translated PDF"
              />
            </div>
          </div>
        )}

      </div>

      {/* Helper Text */}
      <p className="text-center text-xs text-gray-500">
        💡 Tip: Use the tabs above to switch between different views
      </p>

    </div>
  );
}