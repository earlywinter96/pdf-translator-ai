// components/FileUploaderWithPayment.tsx
/**
 * File Uploader with Payment Integration
 * Updated for Sarvam AI (22+ languages)
 */

"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, Languages, Zap, AlertCircle } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { usePayment } from "@/app/usepayment";
import PaymentModal from "@/components/PaymentModal";
import { uploadPDFForTranslation, SUPPORTED_LANGUAGES, PRIMARY_LANGUAGES, EXTENDED_LANGUAGES } from "@/lib/api";

const MAX_FILE_SIZE_MB = 25;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface Props {
  onJobCreated: (jobId: string) => void;
}

interface PaymentInfo {
  requires_payment: boolean;
  free_pages: number;
  paid_pages: number;
  amount_inr: number;
}

export default function FileUploaderWithPayment({ onJobCreated }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [sourceLanguage, setSourceLanguage] = useState("gujarati");
  const [targetLanguage, setTargetLanguage] = useState("english");
  const [translationMode, setTranslationMode] = useState("formal");
  const [showExtendedLanguages, setShowExtendedLanguages] = useState(false);
  
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null);
  const [pendingJobId, setPendingJobId] = useState<string | null>(null);

  const {
    sessionId,
    freePagesRemaining,
    paymentConfig,
    checkPaymentRequired,
    initiatePayment,
  } = usePayment();

  // ============================================================================
  // FILE UPLOAD
  // ============================================================================

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const uploadedFile = acceptedFiles[0];
    
    if (!uploadedFile) return;
    
    if (uploadedFile.size > MAX_FILE_SIZE_BYTES) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE_MB}MB`);
      return;
    }
    
    if (!uploadedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }
    
    setFile(uploadedFile);
    setError(null);
    console.log('📄 File selected:', uploadedFile.name);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    multiple: false,
  });

  // ============================================================================
  // TRANSLATION SUBMISSION
  // ============================================================================

  const handleTranslate = async () => {
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    if (!sessionId) {
      setError('Payment system not initialized. Please refresh.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      console.log('🚀 Starting translation process...');
      console.log('   Source:', sourceLanguage);
      console.log('   Target:', targetLanguage);
      console.log('   Mode:', translationMode);
      console.log('   Translator: Sarvam AI');
      
      // Upload PDF
      const result = await uploadPDFForTranslation({
        file,
        source_language: sourceLanguage,
        target_language: targetLanguage,
        mode: translationMode,
      });

      const jobId = result.job_id;
      setPendingJobId(jobId);

      // Check if payment required
      const pageCount = result.page_count || 0;
      
      if (pageCount > 0) {
        const paymentCheck = await checkPaymentRequired(pageCount);
        
        if (paymentCheck.requires_payment) {
          console.log('💳 Payment required:', paymentCheck);
          setPaymentInfo(paymentCheck);
          setShowPaymentModal(true);
        } else {
          console.log('✅ No payment needed - starting translation');
          onJobCreated(jobId);
        }
      } else {
        onJobCreated(jobId);
      }
    } catch (err: unknown) {
      console.error('❌ Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // ============================================================================
  // PAYMENT HANDLERS
  // ============================================================================

  const handlePaymentSuccess = () => {
    if (pendingJobId) {
      console.log('✅ Payment successful - starting translation');
      onJobCreated(pendingJobId);
    }
  };

  const handlePaymentModalClose = () => {
    setShowPaymentModal(false);
    setIsUploading(false);
  };

  // ============================================================================
  // LANGUAGE SWITCHING
  // ============================================================================

  const swapLanguages = () => {
    const temp = sourceLanguage;
    setSourceLanguage(targetLanguage);
    setTargetLanguage(temp);
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-indigo-500/10 border border-cyan-500/20">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-cyan-300 font-medium">
            Powered by Sarvam AI
          </span>
        </div>
        <h1 className="text-4xl font-bold text-white">
          PDF Translation
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Translate PDFs in 22+ Indian languages with AI-powered accuracy
        </p>
      </div>

      {/* Language Selection */}
      <div className="rounded-2xl bg-gradient-to-br from-white/5 to-white/10 border border-white/10 p-6 space-y-4">
        <div className="flex items-center gap-2 text-white font-medium">
          <Languages className="w-5 h-5 text-cyan-400" />
          <span>Translation Settings</span>
        </div>

        <div className="grid md:grid-cols-3 gap-4 items-end">
          {/* Source Language */}
          <div className="space-y-2">
            <label className="text-sm text-gray-400">From</label>
            <select
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:outline-none transition"
            >
              <optgroup label="Primary Languages">
                {PRIMARY_LANGUAGES.map(lang => (
                  <option key={lang} value={lang}>
                    {SUPPORTED_LANGUAGES[lang as keyof typeof SUPPORTED_LANGUAGES].name}
                  </option>
                ))}
              </optgroup>
              
              {showExtendedLanguages && (
                <optgroup label="Extended Languages (via Sarvam AI)">
                  {EXTENDED_LANGUAGES.map(lang => (
                    <option key={lang} value={lang}>
                      {SUPPORTED_LANGUAGES[lang as keyof typeof SUPPORTED_LANGUAGES].name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
            
            {!showExtendedLanguages && (
              <button
                onClick={() => setShowExtendedLanguages(true)}
                className="text-xs text-cyan-400 hover:text-cyan-300"
              >
                + Show 8 more languages
              </button>
            )}
          </div>

          {/* Swap Button */}
          <div className="flex justify-center">
            <button
              onClick={swapLanguages}
              className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition group"
              title="Swap languages"
            >
              <svg
                className="w-5 h-5 text-gray-400 group-hover:text-cyan-400 transition"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
                />
              </svg>
            </button>
          </div>

          {/* Target Language */}
          <div className="space-y-2">
            <label className="text-sm text-gray-400">To</label>
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:outline-none transition"
            >
              <optgroup label="Primary Languages">
                {PRIMARY_LANGUAGES.map(lang => (
                  <option key={lang} value={lang}>
                    {SUPPORTED_LANGUAGES[lang as keyof typeof SUPPORTED_LANGUAGES].name}
                  </option>
                ))}
              </optgroup>
              
              {showExtendedLanguages && (
                <optgroup label="Extended Languages (via Sarvam AI)">
                  {EXTENDED_LANGUAGES.map(lang => (
                    <option key={lang} value={lang}>
                      {SUPPORTED_LANGUAGES[lang as keyof typeof SUPPORTED_LANGUAGES].name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        </div>

        {/* Translation Mode */}
        <div className="space-y-2">
          <label className="text-sm text-gray-400">Translation Style</label>
          <div className="flex gap-2">
            <button
              onClick={() => setTranslationMode("formal")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                translationMode === "formal"
                  ? "bg-cyan-500/20 border-2 border-cyan-500 text-cyan-300"
                  : "bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10"
              }`}
            >
              Formal
            </button>
            <button
              onClick={() => setTranslationMode("general")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                translationMode === "general"
                  ? "bg-cyan-500/20 border-2 border-cyan-500 text-cyan-300"
                  : "bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10"
              }`}
            >
              General
            </button>
            <button
              onClick={() => setTranslationMode("casual")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                translationMode === "casual"
                  ? "bg-cyan-500/20 border-2 border-cyan-500 text-cyan-300"
                  : "bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10"
              }`}
            >
              Casual
            </button>
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div
        {...getRootProps()}
        className={`
          relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
          transition-all duration-300
          ${
            isDragActive
              ? "border-cyan-500 bg-cyan-500/10 scale-105"
              : file
              ? "border-green-500/50 bg-green-500/5"
              : "border-white/20 bg-white/5 hover:border-cyan-500/50 hover:bg-white/10"
          }
        `}
      >
        <input {...getInputProps()} />

        {file ? (
          <div className="space-y-3">
            <FileText className="w-12 h-12 mx-auto text-green-400" />
            <div>
              <p className="text-white font-medium">{file.name}</p>
              <p className="text-sm text-gray-400">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <p className="text-xs text-gray-500">
              Click or drag to replace
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload className="w-12 h-12 mx-auto text-gray-400" />
            <div>
              <p className="text-white font-medium">
                {isDragActive ? "Drop your PDF here" : "Upload PDF"}
              </p>
              <p className="text-sm text-gray-400 mt-1">
                Click to browse or drag and drop
              </p>
            </div>
            <p className="text-xs text-gray-500">
              Maximum file size: {MAX_FILE_SIZE_MB}MB
            </p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Free Pages Info */}
      {paymentConfig && (
        <div className="text-center text-sm text-gray-400">
          You have{" "}
          <span className="font-semibold text-cyan-400">
            {freePagesRemaining}
          </span>{" "}
          free pages remaining this session
        </div>
      )}

      {/* Translate Button */}
      <button
        onClick={handleTranslate}
        disabled={!file || isUploading || !sessionId}
        className="w-full py-4 rounded-xl font-semibold text-white
          bg-gradient-to-r from-indigo-600 to-cyan-600
          hover:from-indigo-500 hover:to-cyan-500
          disabled:opacity-50 disabled:cursor-not-allowed
          transition shadow-lg hover:shadow-cyan-500/25
          flex items-center justify-center gap-2"
      >
        {isUploading ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            <Zap className="w-5 h-5" />
            <span>Translate PDF</span>
          </>
        )}
      </button>

      {/* Payment Modal */}
      {showPaymentModal && paymentInfo && pendingJobId && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={handlePaymentModalClose}
          onPaymentSuccess={handlePaymentSuccess}
          pageCount={paymentInfo.free_pages + paymentInfo.paid_pages}
          paymentAmount={paymentInfo.amount_inr}
          freePagesUsed={paymentInfo.free_pages}
          paidPages={paymentInfo.paid_pages}
          jobId={pendingJobId}
          initiatePayment={initiatePayment}
          isDemoMode={paymentConfig?.demo_mode}
        />
      )}
    </div>
  );
}
