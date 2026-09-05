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

type SelectedPlan = {
  id: string;
  name: string;
  price: number;
  pageLimit: number;
  limits: string;
};

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
  const [sourceLanguage, setSourceLanguage] = useState("Gujarati");
  const [targetLanguage, setTargetLanguage] = useState("English");
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jobStatus, setJobStatus] = useState<string>("");
  const [previewPayment, setPreviewPayment] = useState<PaymentQuote | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [planMessage, setPlanMessage] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<SelectedPlan | null>(null);
  const [completedPageLimit, setCompletedPageLimit] = useState<number | null>(null);
  const [documentPageCount, setDocumentPageCount] = useState(0);
  const [paidAmountTotal, setPaidAmountTotal] = useState(0);
  const [fullDocumentPrice, setFullDocumentPrice] = useState(0);
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
  const pollGenerationRef = useRef<number>(0);
  // Keep the known-good one-page preview on screen while the paid worker is
  // producing its separate PDF. Switching the iframe too early makes native
  // PDF viewers retain the old preview/lock page after payment.
  const awaitingPaidOutputRef = useRef<boolean>(false);

  /* ============================================================================
     POLLING EFFECT
  ============================================================================ */
  useEffect(() => {
    if (!jobId) return;

    const pollingRun = ++pollGenerationRef.current;
    isActiveRef.current = true;
    failureCountRef.current = 0;
    let pollCounter = 0;
    let timeoutId: NodeJS.Timeout | null = null;

    const pollStatus = async () => {
      if (!isActiveRef.current || pollingRun !== pollGenerationRef.current) return;

      try {
        pollCounter++;
        setPollCount(pollCounter);
        setLastPollTime(new Date().toISOString());

        const data = await getJobStatus(jobId);

        // A preview request can resolve after payment has started. Ignore that
        // stale "completed" response so it can never replace the active paid
        // processing status with a premature ready screen.
        if (!isActiveRef.current || pollingRun !== pollGenerationRef.current) return;

        setProgress(data.progress);
        setStatusMessage(data.message);
        setJobStatus(data.status);

        // -------------------------------
        // STOP CONDITIONS
        // -------------------------------
        if (data.status === "completed" || data.progress >= 100) {
          if (awaitingPaidOutputRef.current) {
            if (data.output_kind !== "paid_unlock") {
              // A payment callback and its worker can reach Render just after
              // the final preview poll. Keep the customer on processing until
              // the paid worker writes its own output marker (or truly fails).
              setJobStatus("processing");
              setStatusMessage("Payment confirmed. Preparing your paid pages…");
              timeoutId = setTimeout(pollStatus, POLL_INTERVAL_MS);
              return;
            }
            awaitingPaidOutputRef.current = false;
            // This changes BilingualPreview from ?version=preview to
            // ?version=paid only after the paid file exists on Render.
            setPreviewPayment(null);
          }
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
    selectedSourceLanguage: string,
    selectedTargetLanguage: string,
    payment?: PaymentQuote,
  ) => {
    setJobId(id);
    setPreviewPayment(payment ?? null);
    setDocumentPageCount(payment ? payment.free_pages + payment.paid_pages : 0);
    setFullDocumentPrice(payment?.full_pdf_amount_inr ?? payment?.amount_inr ?? 0);
    setPaidAmountTotal(0);
    setPlanMessage(null);
    setSelectedPlan(null);
    setSourceLanguage(
      selectedSourceLanguage.charAt(0).toUpperCase() + selectedSourceLanguage.slice(1)
    );
    setTargetLanguage(
      selectedTargetLanguage.charAt(0).toUpperCase() + selectedTargetLanguage.slice(1)
    );
    setProgress(0);
    setStatusMessage("Starting translation...");
    setJobStatus("processing");
    setFailureCount(0);
    setPollCount(0);
    setStuckDetected(false);
    awaitingPaidOutputRef.current = false;
    lastProgressUpdateRef.current = Date.now();
  };

  const handlePaymentSuccess = async (orderId: string) => {
    if (!jobId) return;
    // Invalidate an in-flight preview poll immediately, before it can report
    // the old completed preview state while checkout starts paid processing.
    pollGenerationRef.current += 1;
    awaitingPaidOutputRef.current = true;
    // Do not switch the PDF viewer away from the preview until the server has
    // accepted the verified order and confirms the exact paid page limit.
    try {
      const started = await startPaidTranslation(jobId, orderId);
      const serverPageLimit = Number(started?.page_limit);
      if (!Number.isInteger(serverPageLimit) || serverPageLimit <= 1) {
        throw new Error("Payment was verified, but the selected page package could not be started. Please contact support.");
      }
      setCompletedPageLimit(serverPageLimit);
      setPaidAmountTotal(Number(started?.paid_amount_total) / 100 || paidAmountTotal + (selectedPlan?.price ?? previewPayment?.amount_inr ?? 0));
    } catch (error) {
      awaitingPaidOutputRef.current = false;
      throw error;
    }
    // Do not clear previewPayment yet. The polling loop clears it only after
    // Render reports the separate paid output as completed.
    setShowPaymentModal(false);
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
    setPlanMessage(null);
    setSelectedPlan(null);
    setCompletedPageLimit(null);
    setDocumentPageCount(0);
    setPaidAmountTotal(0);
    setFailureCount(0);
    setPollCount(0);
    setStuckDetected(false);
    awaitingPaidOutputRef.current = false;
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
              {previewPayment
                ? "Your Free 1-Page Preview Is Ready"
                : completedPageLimit
                  ? `Your ${completedPageLimit}-Page Translation Is Ready 🎉`
                  : "Your Design-Preserved Translation Is Ready 🎉"}
            </h2>
            {previewPayment ? (
              <div className="mx-auto max-w-xl rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/15 to-indigo-500/10 p-6 text-left shadow-xl shadow-cyan-950/30">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-lg font-semibold text-white">Check the first-page translation before you pay</p>
                    <p className="mt-1 text-xs font-medium uppercase tracking-[0.16em] text-cyan-300">No hidden processing after preview</p>
                  </div>
                  <span className="shrink-0 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-sm font-semibold text-cyan-200">₹{(selectedPlan?.price ?? previewPayment.amount_inr).toFixed(0)}</span>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-gray-300">
                  Your {previewPayment.free_pages + previewPayment.paid_pages}-page PDF has a free first-page preview. The remaining pages have not been sent to Sarvam AI. Choose how many pages you want to unlock.
                </p>
                <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl border border-white/10 bg-slate-950/30 p-4 text-sm">
                  <div><p className="text-gray-500">Document</p><p className="mt-1 font-semibold text-white">{previewPayment.free_pages + previewPayment.paid_pages} pages</p></div>
                  <div><p className="text-gray-500">Selected unlock</p><p className="mt-1 font-semibold text-cyan-300">{selectedPlan ? `${selectedPlan.pageLimit} pages · ₹${selectedPlan.price.toFixed(0)}` : `${Math.min(previewPayment.package_limit_pages || previewPayment.free_pages + previewPayment.paid_pages, previewPayment.free_pages + previewPayment.paid_pages)} pages · ₹${previewPayment.amount_inr.toFixed(0)}`}</p></div>
                </div>
                <div className="mt-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">Transparent plans</p>
                    <span className="text-xs text-gray-400">Choose what you need</span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
                    {[...(previewPayment.available_packages || []).map((plan) => ({
                      id: plan.id,
                      name: plan.name,
                      limit: plan.page_limit,
                      price: plan.amount_inr,
                      limits: `First ${plan.page_limit} pages`,
                    })), {
                      id: "full_pdf",
                      name: "Full PDF",
                      limit: previewPayment.free_pages + previewPayment.paid_pages,
                      price: previewPayment.full_pdf_amount_inr ?? previewPayment.amount_inr,
                      limits: "All document pages",
                    }].filter((plan, _, plans) => {
                      const pageCount = previewPayment.free_pages + previewPayment.paid_pages;
                      if (plan.id !== "full_pdf") return plan.limit <= pageCount;
                      return !plans.some((candidate) => candidate.id !== "full_pdf" && candidate.limit >= pageCount);
                    }).map((plan) => {
                      const pageCount = previewPayment.free_pages + previewPayment.paid_pages;
                      const pageLimit = Math.min(plan.limit, pageCount);
                      const selected = selectedPlan?.id === plan.id || (!selectedPlan && plan.id === previewPayment.package_id);
                      return (
                        <button
                          type="button"
                          key={plan.id}
                          onClick={() => {
                            setSelectedPlan({ id: plan.id, name: plan.name, price: plan.price, pageLimit, limits: plan.limits });
                            setPlanMessage(`${plan.name} selected: you will receive a translated PDF with the first ${pageLimit} page${pageLimit === 1 ? "" : "s"}.`);
                          }}
                          className={`rounded-lg border p-2.5 text-left transition focus:outline-none focus:ring-2 focus:ring-cyan-300 ${selected ? "border-cyan-400/70 bg-cyan-400/10 hover:bg-cyan-400/20" : "border-white/10 bg-white/[0.03] hover:border-cyan-400/40 hover:bg-white/[0.06]"}`}
                          aria-label={`Select ${plan.name}, ₹${plan.price}`}
                        >
                          <p className={`text-xs font-semibold ${selected ? "text-cyan-200" : "text-gray-200"}`}>{plan.name}</p>
                          <p className="mt-1 min-h-8 text-[11px] text-gray-500">{plan.limits}</p>
                          <p className="mt-1 text-sm font-bold text-white">₹{plan.price.toFixed(0)}</p>
                          <p className={`mt-1 text-[10px] font-medium ${selected ? "text-cyan-300" : "text-gray-500"}`}>{selected ? "Selected" : "Select plan"}</p>
                        </button>
                      );
                    })}
                  </div>
                  <p className="mt-2 text-xs text-gray-500">Only plans that fit this document's page and text limits are shown. Each plan includes your free preview page.</p>
                  {planMessage && <p role="status" className="mt-2 rounded-lg border border-amber-400/30 bg-amber-400/10 p-2 text-xs leading-relaxed text-amber-100">{planMessage}</p>}
                </div>
                {previewPayment.pricing_model === "full_pdf_character_based" && (
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
                  <CreditCard className="h-5 w-5" /> Pay ₹{(selectedPlan?.price ?? previewPayment.amount_inr).toFixed(0)} securely with Razorpay
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-cyan-100">
                  Translation: <span className="font-semibold text-white">{sourceLanguage}</span>
                  <span className="mx-2 text-cyan-400">→</span>
                  <span className="font-semibold text-white">{targetLanguage}</span>
                </p>
                {completedPageLimit && (
                  <p className="text-sm text-cyan-200">Your selected plan includes the first {completedPageLimit} page{completedPageLimit === 1 ? "" : "s"}. Download the translated result below.</p>
                )}
                {completedPageLimit && completedPageLimit < documentPageCount && (
                  <div className="mx-auto max-w-xl rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4 text-left">
                    <p className="font-semibold text-white">Need more pages?</p>
                    <p className="mt-1 text-sm text-gray-300">Choose a larger page range. You pay only the upgrade difference, then we regenerate the expanded PDF.</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {[
                        { id: "starter", name: "2 pages", limit: 2, total: 5 },
                        { id: "basic", name: "5 pages", limit: 5, total: 19 },
                        { id: "standard", name: "8 pages", limit: 8, total: 29 },
                        { id: "plus", name: "10 pages", limit: 10, total: 39 },
                        { id: "full_pdf", name: "full document", limit: documentPageCount, total: fullDocumentPrice },
                      ].filter((plan) => plan.limit > completedPageLimit && plan.limit <= documentPageCount && (plan.id !== "full_pdf" || documentPageCount > 10)).map((plan) => {
                        const upgradePrice = Math.max(1, plan.total - paidAmountTotal);
                        return <button key={plan.id} onClick={() => { setSelectedPlan({ id: plan.id, name: plan.name, price: upgradePrice, pageLimit: plan.limit, limits: `First ${plan.limit} pages` }); setShowPaymentModal(true); }} className="rounded-lg border border-cyan-400/40 px-3 py-2 text-sm font-medium text-cyan-100 hover:bg-cyan-400/15">Unlock {plan.name} · ₹{upgradePrice}</button>;
                      })}
                    </div>
                  </div>
                )}
                <div className="flex justify-center gap-3">
                <DownloadButton jobId={jobId} />
                <button onClick={handleReset} className="border px-4 py-2 rounded-lg text-white">
                  Translate Another
                </button>
                </div>
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

      {jobId && (previewPayment || completedPageLimit) && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          onCancel={() => {
            void reportPaymentEvent(jobId, "payment_modal_dismissed");
            setShowPaymentModal(false);
          }}
          onPaymentSuccess={handlePaymentSuccess}
          pageCount={documentPageCount || (previewPayment?.free_pages ?? 0) + (previewPayment?.paid_pages ?? 0)}
          paymentAmount={selectedPlan?.price ?? previewPayment?.amount_inr ?? 0}
          freePagesUsed={completedPageLimit ?? previewPayment?.free_pages ?? 1}
          jobId={jobId}
          packageName={selectedPlan?.name ?? previewPayment?.package_name ?? "Full PDF"}
          packageId={selectedPlan?.id ?? previewPayment?.package_id ?? "full_pdf"}
          pageLimit={selectedPlan?.pageLimit ?? documentPageCount}
          initiatePayment={initiatePayment}
          isDemoMode={paymentConfig?.demo_mode}
        />
      )}
    </main>
  );
}
