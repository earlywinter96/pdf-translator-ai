"use client";

import { downloadTranslatedPDF } from "@/lib/api";

export default function DownloadButton({ jobId }: { jobId: string }) {
  return (
    <button
      onClick={() => downloadTranslatedPDF(jobId)}
      className="px-6 py-2.5 rounded-md text-white font-medium
        bg-gradient-to-r from-emerald-600 to-green-600
        hover:from-emerald-500 hover:to-green-500
        transition shadow-lg"
    >
      Download Translated PDF
    </button>
  );
}
