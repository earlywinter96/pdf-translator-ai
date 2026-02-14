// app/visualize/page.tsx
"use client";

import { useState } from "react";
import { ArrowLeft, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import VisualizationUploader from "@/components/VisualizationUploader";
import VisualizationDisplay from "@/components/VisualizationDisplay";
import { getJobStatus } from "@/lib/api";

const POLL_INTERVAL_MS = 3000;
const MAX_FAILURES = 5;

export default function VisualizePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobStatus, setJobStatus] = useState<string>("");
  const [failureCount, setFailureCount] = useState(0);
  const [pollCount, setPollCount] = useState(0);

  // Session ID (you may want to use the same payment hook)
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let sid = sessionStorage.getItem('session_id');
      if (!sid) {
        sid = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('session_id', sid);
      }
      return sid;
    }
    return null;
  });

  // Poll status
  const pollStatus = async (currentJobId: string) => {
    try {
      setPollCount(prev => prev + 1);
      
      const data = await getJobStatus(currentJobId);
      
      setProgress(data.progress);
      setStatusMessage(data.message);
      setJobStatus(data.status);
      
      // Reset failure count on success
      setFailureCount(0);
      
      // Check if complete
      if (data.status === "completed" || data.progress >= 100) {
        setJobStatus("completed");
        return; // Stop polling
      }
      
      if (data.status === "failed") {
        setJobStatus("failed");
        return; // Stop polling
      }
      
      // Continue polling
      setTimeout(() => pollStatus(currentJobId), POLL_INTERVAL_MS);
      
    } catch (err) {
      setFailureCount(prev => prev + 1);
      
      if (failureCount >= MAX_FAILURES) {
        setJobStatus("failed");
        setStatusMessage("Failed to connect to server. Please try again.");
      } else {
        // Retry
        setTimeout(() => pollStatus(currentJobId), POLL_INTERVAL_MS);
      }
    }
  };

  const handleJobCreated = (id: string) => {
    setJobId(id);
    setProgress(0);
    setStatusMessage("Starting visualization...");
    setJobStatus("processing");
    setFailureCount(0);
    setPollCount(0);
    
    // Start polling
    setTimeout(() => pollStatus(id), 2000);
  };

  const handleReset = () => {
    setJobId(null);
    setProgress(0);
    setStatusMessage("");
    setJobStatus("");
    setFailureCount(0);
    setPollCount(0);
  };

  const getFriendlyMessage = () => {
    if (statusMessage) return statusMessage;
    
    if (progress < 15) return "Checking PDF language...";
    if (progress < 30) return "Extracting text...";
    if (progress < 70) return "Analyzing content structure...";
    if (progress < 95) return "Generating visual data...";
    return "Finalizing...";
  };

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">
      
      {/* Back button */}
      {jobId && (
        <div className="max-w-4xl mx-auto pt-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      )}

      <div className="relative max-w-4xl mx-auto pt-28 pb-24 space-y-14">
        
        {/* Upload Form */}
        {!jobId && (
          <VisualizationUploader 
            onJobCreated={handleJobCreated}
            sessionId={sessionId || undefined}
          />
        )}

        {/* Processing Status */}
        {jobId && jobStatus !== "completed" && jobStatus !== "failed" && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-white/5 p-8 text-center space-y-4">
              <Loader2 className="w-10 h-10 mx-auto animate-spin text-purple-400" />
              <p className="text-white text-lg">{getFriendlyMessage()}</p>
              
              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="relative w-full h-3 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-400 to-pink-500 transition-all duration-500 rounded-full"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              <p className="text-xs text-gray-500">
                Polls: {pollCount}
              </p>

              {failureCount > 0 && (
                <p className="text-xs text-yellow-400">
                  ⚠️ Connection issues ({failureCount}/{MAX_FAILURES})
                </p>
              )}
            </div>

            {/* Info While Waiting */}
            <div className="rounded-xl bg-blue-500/5 border border-blue-500/20 p-6">
              <h3 className="text-white font-semibold mb-3">What's happening?</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="text-blue-400">•</span>
                  <span>AI is analyzing your document structure</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400">•</span>
                  <span>Extracting key concepts and relationships</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400">•</span>
                  <span>Creating visual data mappings</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400">•</span>
                  <span>Generating concept maps and timelines</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Completed - Show Visualization */}
        {jobStatus === "completed" && jobId && (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <CheckCircle className="w-16 h-16 mx-auto text-green-400" />
              <h2 className="text-white text-2xl font-bold">
                Visualization Complete! 🎉
              </h2>
              <button
                onClick={handleReset}
                className="px-6 py-2 rounded-lg border border-white/20 text-white hover:bg-white/5 transition"
              >
                Visualize Another Document
              </button>
            </div>

            <VisualizationDisplay jobId={jobId} />
          </div>
        )}

        {/* Failed */}
        {jobStatus === "failed" && (
          <div className="text-center space-y-4">
            <AlertCircle className="w-16 h-16 mx-auto text-red-400" />
            <h2 className="text-white text-xl font-semibold">Visualization Failed</h2>
            <p className="text-gray-400">{statusMessage}</p>
            <button
              onClick={handleReset}
              className="px-6 py-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-white transition"
            >
              Try Again
            </button>
          </div>
        )}

      </div>
    </main>
  );
}