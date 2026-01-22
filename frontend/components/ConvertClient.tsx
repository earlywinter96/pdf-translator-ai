"use client";

import { useEffect, useState } from "react";
import FileUploader from "@/components/FileUploader";
import ProgressBar from "@/components/ProgressBar";
import DownloadButton from "@/components/DownloadButton";
import { getJobStatus } from "@/lib/api";
import BilingualPreview from "@/components/BilingualPreview";

export default function ConvertClient() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobStatus, setJobStatus] = useState<string>("");

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      const data = await getJobStatus(jobId);
      setProgress(data.progress);
      setStatusMessage(data.message);
      setJobStatus(data.status);

      if (data.status === "completed" || data.status === "failed") {
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      {/* Content */}
      <div className="relative max-w-4xl mx-auto pt-28 pb-24 space-y-14">

        {/* Upload Card */}
        <div className="mx-auto max-w-md rounded-2xl bg-white/5 backdrop-blur-md
          border border-white/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)]
          overflow-hidden">

          <div className="h-[2px] bg-gradient-to-r from-cyan-500/60 to-indigo-500/60" />

          <div className="p-8 space-y-6">
            <h2 className="text-base font-medium text-gray-200 text-center tracking-wide">
              <b>Upload PDF for Translation</b>
              <p className="text-xs text-gray-500 mt-1">
                Files are processed temporarily and automatically deleted.
              </p>
            </h2>

            {!jobId && <FileUploader onJobCreated={setJobId} />}

            {jobId && (
              <div className="space-y-4">
                <p className="text-sm text-gray-400 text-center">
                  {statusMessage}
                </p>
                <ProgressBar progress={progress} />
              </div>
            )}

            {jobStatus === "completed" && jobId && (
              <div className="flex justify-center pt-2">
                <DownloadButton jobId={jobId} />
              </div>
            )}
          </div>
        </div>

        {/* Preview */}
        {jobStatus === "completed" && jobId && (
          <div className="max-w-7xl mx-auto space-y-4">
            <h3 className="text-white font-medium text-center text-lg">
              Side-by-Side Preview
            </h3>
            <BilingualPreview jobId={jobId} />
          </div>
        )}

      </div>
    </main>
  );
}
