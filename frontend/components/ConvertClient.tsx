"use client";

import { useEffect, useState } from "react";
import { CheckCircle, AlertCircle, RotateCcw, Loader2 } from "lucide-react";
import FileUploader from "@/components/FileUploader";
import ProgressBar from "@/components/ProgressBar";
import DownloadButton from "@/components/DownloadButton";
import BilingualPreview from "@/components/BilingualPreview";
import { getJobStatus } from "@/lib/api";
import TranslationFeedback from "@/components/TranslationFeedback";


export default function ConvertClient() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobStatus, setJobStatus] = useState<string>("");

  // Poll job status
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

  // Reset to upload another file
  const handleReset = () => {
    setJobId(null);
    setProgress(0);
    setStatusMessage("");
    setJobStatus("");
  };

  // Get user-friendly status message
  const getFriendlyMessage = () => {
    if (statusMessage) return statusMessage;
    
    if (progress < 30) return "Extracting text from PDF...";
    if (progress < 70) return "Translating content...";
    return "Finalizing document...";
  };

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      {/* Content */}
      <div className="relative max-w-4xl mx-auto pt-28 pb-24 space-y-14">

        {/* UPLOAD STATE - Show when no job */}
        {!jobId && (
          <div className="mx-auto max-w-md rounded-2xl bg-white/5 backdrop-blur-md
            border border-white/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)]
            overflow-hidden">

            <div className="h-[2px] bg-gradient-to-r from-cyan-500/60 to-indigo-500/60" />

            <div className="p-8 space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold text-white mb-2">
                  Upload PDF for Translation
                </h2>
                <p className="text-xs text-gray-500">
                  Files are processed temporarily and automatically deleted
                </p>
              </div>

              <FileUploader onJobCreated={setJobId} />
            </div>
          </div>
        )}

        {/* PROCESSING STATE - Show while job is running */}
        {jobId && jobStatus !== "completed" && jobStatus !== "failed" && (
          <div className="mx-auto max-w-2xl rounded-2xl bg-white/5 backdrop-blur-md
            border border-white/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)]
            overflow-hidden">

            <div className="h-[2px] bg-gradient-to-r from-cyan-500/60 to-indigo-500/60" />

            <div className="p-8 space-y-6">
              
              {/* Status Message with Icon */}
              <div className="text-center space-y-3">
                <Loader2 className="w-10 h-10 mx-auto text-cyan-400 animate-spin" />
                <div>
                  <p className="text-white font-medium text-lg">
                    {getFriendlyMessage()}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    This usually takes 2-3 minutes
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              <ProgressBar progress={progress} />
            </div>
          </div>
        )}

        {/* COMPLETED STATE */}
        {jobStatus === "completed" && jobId && (
          <div className="space-y-8">
            
            {/* Success Card */}
            <div className="mx-auto max-w-2xl rounded-2xl bg-white/5 backdrop-blur-md
              border border-white/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] p-8">
              
              <div className="text-center space-y-6">
                
                {/* Success Icon */}
                <div className="w-16 h-16 mx-auto rounded-full bg-green-500/20 flex items-center justify-center">
                  <CheckCircle className="w-10 h-10 text-green-400" />
                </div>

                {/* Success Message */}
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    Translation Complete!
                  </h2>
                  <p className="text-gray-400">
                    Your PDF has been successfully translated
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
                  <DownloadButton jobId={jobId} />
                  
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 rounded-lg font-medium
                      border border-white/20 text-white
                      hover:bg-white/5 transition
                      flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="w-5 h-5" />
                    Translate Another
                  </button>
                </div>
              </div>
            </div>

            {/* Preview Section */}
            <div className="max-w-7xl mx-auto space-y-4">
              <h3 className="text-white font-semibold text-center text-lg">
                Side-by-Side Preview
              </h3>
              <BilingualPreview jobId={jobId} />
            </div>
            <div className="max-w-2xl mx-auto">
              <TranslationFeedback jobId={jobId} />
            </div>

          </div>
        )}

        {/* FAILED STATE */}
        {jobStatus === "failed" && jobId && (
          <div className="mx-auto max-w-2xl rounded-2xl bg-white/5 backdrop-blur-md
            border border-white/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] p-8">
            
            <div className="text-center space-y-6">
              
              {/* Error Icon */}
              <div className="w-16 h-16 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertCircle className="w-10 h-10 text-red-400" />
              </div>

              {/* Error Message */}
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Translation Failed
                </h2>
                <p className="text-gray-400">
                  {statusMessage || "Something went wrong. Please try again."}
                </p>
              </div>

              {/* Retry Button */}
              <button
                onClick={handleReset}
                className="px-6 py-3 rounded-lg text-white font-medium
                  bg-gradient-to-r from-indigo-600 to-cyan-600
                  hover:from-indigo-500 hover:to-cyan-500
                  transition shadow-lg flex items-center justify-center gap-2 mx-auto"
              >
                <RotateCcw className="w-5 h-5" />
                Try Again
              </button>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}