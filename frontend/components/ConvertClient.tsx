"use client";

import { useEffect, useRef, useState } from "react";
import {
  CheckCircle,
  AlertCircle,
  RotateCcw,
  Loader2,
  ArrowLeft,
  CreditCard,
} from "lucide-react";
import Link from "next/link";

import FileUploaderWithPayment from "@/components/FileUploaderWithPayment";
import ProgressBar from "@/components/ProgressBar";
import DownloadButton from "@/components/DownloadButton";
import BilingualPreview from "@/components/BilingualPreview";
import WaitingTimeFiller from "@/components/WaitingTimeFiller";
import TranslationFeedback from "@/components/TranslationFeedback";
import PaymentModal from "@/components/PaymentModal";
import { getJobStatus, startPaidTranslation } from "@/lib/api";
import { usePayment } from "@/app/usepayment";
import type { PaymentQuote } from "@/components/FileUploaderWithPayment";

/* ============================================================================
   CONFIG CONSTANTS (SINGLE SOURCE OF TRUTH)
============================================================================ */
const POLL_INTERVAL_MS = 2000; // fallback retry delay
const MAX_FAILURES = 5;
const STUCK_THRESHOLD_MS = 180000; // 3 minutes

function getPollInterval(progress: number) {
  if (progress < 30) return 3000;
  if (progress < 70) return 4000;
  return 7000;
}

export default function ConvertClient() {
  /* ============================================================================
     STATE
  ============================================================================ */
  const [jobId, setJobId] = useState<string | null>(null);
  const [targetLanguage, setTargetLanguage] = useState("English");
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobStatus, setJobStatus] = useState<string>("");
  const [previewPayment, setPreviewPayment] = useState<PaymentQuote | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [translationRun, setTranslationRun] = useState(0);
  const { initiatePayment, paymentConfig, reportPaymentEvent } = usePayment();

  const [failureCount, setFailureCount] = useState(0);
  const [stuckDetected, setStuckDetected] = useState(false);

  const [pollCount, setPollCount] = useState(0);
  const [lastPollTime, setLastPollTime] = useState("");

  /* ============================================================================
     REFS (NO RE-RENDER SIDE EFFECTS)
  ============================================================================ */
  const lastProgressUpdateRef = useRef<number>(Date.now());
  const isActiveRef = useRef<boolean>(false);
  const failureCountRef = useRef<number>(0);

  /* ============================================================================
     POLLING EFFECT
  ============================================================================ */
  useEffect(() => {
    if (!jobId) return;

    isActiveRef.current = true;
    failureCountRef.current = 0;
    let pollCounter = 0;
    let timeoutId: NodeJS.Timeout | null = null;

    const pollStatus = async () => {
      if (!isActiveRef.current) return;

      try {
        pollCounter++;
        setPollCount(pollCounter);
        setLastPollTime(new Date().toISOString());

        const data = await getJobStatus(jobId);

        setProgress(data.progress);
        setStatusMessage(data.message);
        setJobStatus(data.status);

        // -------------------------------
        // STOP CONDITIONS
        // -------------------------------
        if (data.status === "completed" || data.progress >= 100) {
          setJobStatus("completed");
          isActiveRef.current = false;
          return;
        }

        if (data.status === "failed") {
          setJobStatus("failed");
          isActiveRef.current = false;
          return;
        }

        // -------------------------------
        // RESET FAILURE COUNT ON SUCCESS
        // -------------------------------
        failureCountRef.current = 0;
        setFailureCount(0);

        // -------------------------------
        // STUCK DETECTION
        // -------------------------------
        if (data.progress > 0 && data.progress < 100) {
          const now = Date.now();
          const diff = now - lastProgressUpdateRef.current;

          if (diff > STUCK_THRESHOLD_MS) {
            setStuckDetected(true);
          } else {
            setStuckDetected(false);
            lastProgressUpdateRef.current = now;
          }
        }

        // -------------------------------
        // SCHEDULE NEXT POLL
        // -------------------------------
        const nextInterval = getPollInterval(data.progress);
        timeoutId = setTimeout(pollStatus, nextInterval);
      } catch (err) {
        failureCountRef.current++;
        setFailureCount(failureCountRef.current);

        if (failureCountRef.current >= MAX_FAILURES) {
          setJobStatus("failed");
          setStatusMessage(
            "Backend is not responding. This may be due to free-tier cold starts. Please retry in a few minutes."
          );
          isActiveRef.current = false;
          return;
        }

        timeoutId = setTimeout(pollStatus, POLL_INTERVAL_MS);
      }
    };

    pollStatus();

    return () => {
      isActiveRef.current = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [jobId, translationRun]);

  /* ============================================================================
     HANDLERS
  ============================================================================ */
  const handleJobCreated = (
    id: string,
    selectedTargetLanguage: string,
    payment?: PaymentQuote,
  ) => {
    setJobId(id);
    setPreviewPayment(payment ?? null);
    setTargetLanguage(
      selectedTargetLanguage.charAt(0).toUpperCase() + selectedTargetLanguage.slice(1)
    );
    setProgress(0);
    setStatusMessage("Starting translation...");
    setJobStatus("processing");
    setFailureCount(0);
    setPollCount(0);
    setStuckDetected(false);
    lastProgressUpdateRef.current = Date.now();
  };

  const handlePaymentSuccess = async (orderId: string) => {
    if (!jobId) return;
    await startPaidTranslation(jobId, orderId);
    setShowPaymentModal(false);
    setPreviewPayment(null);
    setProgress(1);
    setStatusMessage("Payment verified. Starting full-document translation...");
    setJobStatus("processing");
    setTranslationRun((run) => run + 1);
  };

  const handleReset = () => {
    setJobId(null);
    setProgress(0);
    setStatusMessage("");
    setJobStatus("");
    setPreviewPayment(null);
    setShowPaymentModal(false);
    setFailureCount(0);
    setPollCount(0);
    setStuckDetected(false);
  };

  /* ============================================================================
     HELPERS
  ============================================================================ */
  const getFriendlyMessage = () => {
    if (stuckDetected) {
      return "⚠️ Processing is taking longer than expected (free tier servers).";
    }
    if (statusMessage) return statusMessage;

    if (progress < 10) return "Initializing...";
    if (progress < 30) return "Extracting text...";
    if (progress < 60) return "Translating content...";
    if (progress < 90) return "Generating PDF...";
    return "Finalizing...";
  };

  /* ============================================================================
     RENDER
  ============================================================================ */
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">
      {jobId && (
        <div className="max-w-4xl mx-auto pt-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      )}

      <div className="relative max-w-4xl mx-auto pt-28 pb-24 space-y-14">
        {!jobId && (
          <FileUploaderWithPayment onJobCreated={handleJobCreated} />
        )}

        {jobId && jobStatus !== "completed" && jobStatus !== "failed" && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-white/5 p-8 text-center space-y-4">
              <Loader2 className="w-10 h-10 mx-auto animate-spin text-cyan-400" />
              <p className="text-white text-lg">{getFriendlyMessage()}</p>
              <ProgressBar progress={progress} />
              <p className="text-xs text-gray-500">
                Polls: {pollCount} | Last:{" "}
                {lastPollTime
                  ? new Date(lastPollTime).toLocaleTimeString()
                  : "N/A"}
              </p>

              {failureCount > 0 && (
                <p className="text-xs text-yellow-400">
                  ⚠️ Connection issues ({failureCount}/{MAX_FAILURES})
                </p>
              )}
            </div>

            <WaitingTimeFiller progress={progress} />
          </div>
        )}

        {jobStatus === "completed" && jobId && (
          <div className="space-y-6 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400" />
            <h2 className="text-white text-2xl font-bold">
              {previewPayment ? "Your Free 1-Page Preview Is Ready" : "Your Design-Preserved Translation Is Ready 🎉"}
            </h2>
            {previewPayment ? (
              <div className="mx-auto max-w-xl rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-6 text-left">
                <p className="text-lg font-semibold text-white">Check the first-page translation before you pay</p>
                <p className="mt-2 text-sm leading-relaxed text-gray-300">
                  This {previewPayment.free_pages + previewPayment.paid_pages}-page PDF has a free first-page preview. The remaining {previewPayment.paid_pages} page{previewPayment.paid_pages === 1 ? "" : "s"} have not been sent for translation. Unlock the full document for ₹{previewPayment.amount_inr.toFixed(0)} when you are satisfied.
                </p>
                {previewPayment.pricing_model === "character_based" && (
                  <p className="mt-2 text-xs text-cyan-200">
                    {previewPayment.pricing_basis === "scan_estimate"
                      ? `Estimated from ${previewPayment.paid_pages} scanned page${previewPayment.paid_pages === 1 ? "" : "s"}. Locked pages are OCR-read only after payment.`
                      : `${previewPayment.billable_characters.toLocaleString()} characters detected in the remaining pages.`}
                  </p>
                )}
                <button
                  onClick={() => {
                    void reportPaymentEvent(jobId, "payment_modal_opened");
                    setShowPaymentModal(true);
                  }}
                  className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 px-5 py-3 font-semibold text-white hover:from-indigo-500 hover:to-cyan-500"
                >
                  <CreditCard className="h-5 w-5" /> Unlock {previewPayment.paid_pages} Remaining Page{previewPayment.paid_pages === 1 ? "" : "s"}
                </button>
              </div>
            ) : (
              <div className="flex justify-center gap-3">
                <DownloadButton jobId={jobId} />
                <button onClick={handleReset} className="border px-4 py-2 rounded-lg text-white">
                  Translate Another
                </button>
              </div>
            )}
            <BilingualPreview jobId={jobId} targetLanguage={targetLanguage} isPreview={Boolean(previewPayment)} />
            {!previewPayment && <TranslationFeedback jobId={jobId} />}
          </div>
        )}

        {jobStatus === "failed" && (
          <div className="text-center space-y-4">
            <AlertCircle className="w-16 h-16 mx-auto text-red-400" />
            <p className="text-gray-400">{statusMessage}</p>
            <button
              onClick={handleReset}
              className="px-6 py-3 rounded-lg bg-cyan-600 text-white"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      {jobId && previewPayment && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          onCancel={() => {
            void reportPaymentEvent(jobId, "payment_modal_dismissed");
            setShowPaymentModal(false);
          }}
          onPaymentSuccess={handlePaymentSuccess}
          pageCount={previewPayment.free_pages + previewPayment.paid_pages}
          paymentAmount={previewPayment.amount_inr}
          freePagesUsed={previewPayment.free_pages}
          paidPages={previewPayment.paid_pages}
          jobId={jobId}
          initiatePayment={initiatePayment}
          isDemoMode={paymentConfig?.demo_mode}
        />
      )}
    </main>
  );
}
