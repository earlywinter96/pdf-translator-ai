// components/FileUploaderWithPayment.tsx
"use client";

import { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, AlertCircle, Loader2, CheckCircle, X, Info } from 'lucide-react';
import { usePayment } from '@/app/usepayment';
import PaymentModal from './PaymentModal';

interface FileUploaderWithPaymentProps {
  onJobCreated: (jobId: string) => void;
}

export default function FileUploaderWithPayment({
  onJobCreated,
}: FileUploaderWithPaymentProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isCheckingPages, setIsCheckingPages] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  
  // PDF info
  const [pdfPageCount, setPdfPageCount] = useState<number | null>(null);
  
  // Payment modal state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentDetails, setPaymentDetails] = useState<any>(null);

  // Form options
  const [language, setLanguage] = useState('gu');
  const [direction, setDirection] = useState('to_en');
  const [mode, setMode] = useState('general');

  // Payment hook
  const {
    sessionId,
    freePagesRemaining,
    paymentConfig,
    checkPaymentRequired,
    initiatePayment,
  } = usePayment();

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 
    "https://pdf-translator-ai.onrender.com";

  // Debug logging helper
  const addDebugLog = (message: string) => {
    console.log(message);
    setDebugInfo(prev => [...prev.slice(-10), `${new Date().toISOString().split('T')[1].slice(0, 8)} ${message}`]);
  };

  // Check session on mount
  useEffect(() => {
    addDebugLog(`🔧 Component mounted`);
    addDebugLog(`📍 API Base: ${API_BASE}`);
    addDebugLog(`🔑 Session ID: ${sessionId ? sessionId.substring(0, 16) + '...' : 'NOT SET'}`);
    addDebugLog(`📄 Free pages: ${freePagesRemaining}`);
    
    if (!sessionId) {
      setError('Session not initialized. Please refresh the page.');
    }
  }, [sessionId, API_BASE, freePagesRemaining]);

  // ============================================================================
  // FILE HANDLING
  // ============================================================================

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setPdfPageCount(null);
      setError(null);
      addDebugLog(`📁 File selected: ${droppedFile.name} (${formatFileSize(droppedFile.size)})`);
    } else {
      setError('Please upload a PDF file');
      addDebugLog(`❌ Invalid file type: ${droppedFile?.type}`);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setPdfPageCount(null);
      setError(null);
      addDebugLog(`📁 File selected: ${selectedFile.name} (${formatFileSize(selectedFile.size)})`);
    } else {
      setError('Please upload a PDF file');
      addDebugLog(`❌ Invalid file type: ${selectedFile?.type}`);
    }
  }, []);

  const handleRemoveFile = () => {
    setFile(null);
    setPdfPageCount(null);
    setError(null);
    addDebugLog(`🗑️ File removed`);
  };

  // ============================================================================
  // PAGE COUNT CHECK - ENHANCED ERROR HANDLING
  // ============================================================================

  const checkPdfPageCount = async (pdfFile: File): Promise<number> => {
    addDebugLog('🔍 Starting page count check...');

    if (!sessionId) {
      addDebugLog('❌ No session ID available');
      throw new Error('Session ID not available. Please refresh the page and try again.');
    }

    const formData = new FormData();
    formData.append('file', pdfFile);

    const headers: HeadersInit = {
      'X-Session-ID': sessionId,
    };

    const url = `${API_BASE}/api/check-pdf-pages`;
    addDebugLog(`📡 Request URL: ${url}`);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      addDebugLog(`📥 Response status: ${response.status} ${response.statusText}`);

      // Log all response headers for debugging
      const responseHeaders: any = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });
      addDebugLog(`📋 Response headers: ${JSON.stringify(responseHeaders)}`);

      if (!response.ok) {
        // Try to get the response body in different ways
        let errorMessage = `Server returned ${response.status}`;
        let responseBody: any = null;

        // First, try to clone the response so we can read it multiple times
        const clonedResponse = response.clone();

        try {
          // Try JSON first
          const jsonData = await response.json();
          responseBody = jsonData;
          addDebugLog(`📄 Error response (JSON): ${JSON.stringify(jsonData)}`);
          
          // Extract error message from various possible formats
          if (jsonData.detail) {
            errorMessage = jsonData.detail;
          } else if (jsonData.message) {
            errorMessage = jsonData.message;
          } else if (jsonData.error) {
            errorMessage = jsonData.error;
          } else if (Object.keys(jsonData).length === 0) {
            // Empty JSON object - try to get text instead
            addDebugLog('⚠️ Empty JSON response, trying text...');
            const textData = await clonedResponse.text();
            addDebugLog(`📄 Error response (text): ${textData}`);
            if (textData) {
              errorMessage = textData;
            }
          }
        } catch (jsonError) {
          // Not JSON, try text
          try {
            const textData = await clonedResponse.text();
            addDebugLog(`📄 Error response (text): ${textData}`);
            if (textData) {
              errorMessage = textData;
            }
          } catch (textError) {
            addDebugLog(`❌ Could not read response body`);
          }
        }

        // Add helpful context based on status code
        switch (response.status) {
          case 401:
            errorMessage = 'Session expired or invalid. Please refresh the page.';
            break;
          case 400:
            if (!errorMessage.includes('Bad Request')) {
              errorMessage = errorMessage || 'Invalid PDF file or request.';
            }
            break;
          case 404:
            errorMessage = 'API endpoint not found. Please contact support.';
            addDebugLog(`❌ CRITICAL: Endpoint ${url} not found!`);
            break;
          case 413:
            errorMessage = 'PDF file is too large. Maximum size is 25MB.';
            break;
          case 500:
            errorMessage = 'Server error. Please try again later.';
            break;
          case 503:
            errorMessage = 'Service temporarily unavailable. Please wait a moment and try again.';
            break;
        }

        addDebugLog(`❌ Request failed: ${errorMessage}`);
        throw new Error(errorMessage);
      }

      // Success - parse response
      const data = await response.json();
      addDebugLog(`✅ Success response: ${JSON.stringify(data)}`);

      if (typeof data.page_count !== 'number') {
        addDebugLog(`❌ Invalid response format: missing page_count`);
        throw new Error('Invalid response from server: missing page count');
      }

      addDebugLog(`✅ Page count: ${data.page_count}`);
      return data.page_count;

    } catch (error: any) {
      // Network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        addDebugLog(`❌ Network error: ${error.message}`);
        throw new Error('Network error: Unable to connect to server. Please check your internet connection.');
      }
      
      // Rethrow with context
      addDebugLog(`❌ Error in checkPdfPageCount: ${error.message}`);
      throw error;
    }
  };

  // ============================================================================
  // PAYMENT CHECK & UPLOAD FLOW
  // ============================================================================

  const handleUploadClick = async () => {
    if (!file) {
      addDebugLog('❌ No file selected');
      return;
    }

    if (!sessionId) {
      setError('Session not initialized. Please refresh the page.');
      addDebugLog('❌ Cannot upload without session ID');
      return;
    }

    setIsCheckingPages(true);
    setError(null);
    addDebugLog('🚀 Starting upload flow...');

    try {
      // Step 1: Get actual page count from backend
      addDebugLog('📄 Step 1: Checking PDF page count...');
      const pageCount = await checkPdfPageCount(file);
      setPdfPageCount(pageCount);
      addDebugLog(`✅ PDF has ${pageCount} pages`);

      // Step 2: Check if payment is required
      addDebugLog('💳 Step 2: Checking payment requirements...');
      const paymentCheck = await checkPaymentRequired(pageCount);
      addDebugLog(`💳 Payment check result: ${JSON.stringify(paymentCheck)}`);

      setIsCheckingPages(false);

      // Step 3: Show payment modal OR proceed directly
      if (paymentCheck.requires_payment) {
        addDebugLog('💰 Payment required - opening modal');
        setPaymentDetails({ ...paymentCheck, page_count: pageCount });
        setShowPaymentModal(true);
      } else {
        addDebugLog('🆓 Free translation - proceeding to upload');
        await performUpload();
      }
    } catch (err: any) {
      addDebugLog(`❌ Upload flow error: ${err.message}`);
      setIsCheckingPages(false);
      setError(err.message || 'Failed to process PDF. Please try again.');
    }
  };

  const performUpload = async () => {
    if (!file || !sessionId) {
      addDebugLog('❌ Missing file or session ID for upload');
      return;
    }

    setIsUploading(true);
    setError(null);
    addDebugLog('📤 Starting file upload...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', language);
      formData.append('direction', direction);
      formData.append('mode', mode);

      const headers: HeadersInit = {
        'X-Session-ID': sessionId,
      };

      const url = `${API_BASE}/api/upload`;
      addDebugLog(`📡 Upload URL: ${url}`);

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      addDebugLog(`📥 Upload response: ${response.status}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: 'Upload failed'
        }));
        addDebugLog(`❌ Upload error: ${JSON.stringify(errorData)}`);
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      addDebugLog(`✅ Upload successful - Job ID: ${data.job_id}`);
      
      onJobCreated(data.job_id);
      
      // Reset state
      setFile(null);
      setPdfPageCount(null);
      setShowPaymentModal(false);
      addDebugLog('🎉 Upload complete - resetting state');
    } catch (err: any) {
      addDebugLog(`❌ Upload error: ${err.message}`);
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handlePaymentSuccess = async () => {
    addDebugLog('✅ Payment successful - proceeding to upload');
    setShowPaymentModal(false);
    await performUpload();
  };

  // ============================================================================
  // TEST FUNCTIONS (Development only)
  // ============================================================================

  const testBackendConnection = async () => {
    addDebugLog('🧪 Testing backend connection...');
    
    try {
      // Test 1: Health check
      const healthUrl = `${API_BASE}/health`;
      addDebugLog(`📡 Testing: ${healthUrl}`);
      const healthResponse = await fetch(healthUrl);
      addDebugLog(`✅ Health check: ${healthResponse.status}`);
      const healthData = await healthResponse.json();
      addDebugLog(`📄 Health data: ${JSON.stringify(healthData)}`);

      // Test 2: Check if check-pdf-pages endpoint exists
      const checkUrl = `${API_BASE}/api/check-pdf-pages`;
      addDebugLog(`📡 Testing: ${checkUrl} (OPTIONS)`);
      const optionsResponse = await fetch(checkUrl, { method: 'OPTIONS' });
      addDebugLog(`✅ OPTIONS check: ${optionsResponse.status}`);

      setError(null);
      alert('✅ Backend connection OK! Check console for details.');
    } catch (err: any) {
      addDebugLog(`❌ Backend test failed: ${err.message}`);
      setError(`Backend test failed: ${err.message}`);
    }
  };

  const copyDebugInfo = () => {
    const debugText = debugInfo.join('\n');
    navigator.clipboard.writeText(debugText);
    alert('Debug info copied to clipboard!');
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <>
      <div className="space-y-5">
        
        {/* Free Pages Counter */}
        {paymentConfig && (
          <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-cyan-300">
                <span className="font-medium">Free pages remaining:</span>
              </div>
              <div className="text-lg font-bold text-cyan-400">
                {freePagesRemaining} / {paymentConfig.free_pages_limit}
              </div>
            </div>
          </div>
        )}

        {/* Debug Panel (Development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs text-purple-300">
                <Info className="w-4 h-4" />
                <span className="font-medium">Debug Panel</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={copyDebugInfo}
                  className="px-2 py-1 rounded bg-purple-600 hover:bg-purple-500
                    text-xs text-white transition"
                >
                  Copy Logs
                </button>
                <button
                  onClick={testBackendConnection}
                  className="px-2 py-1 rounded bg-purple-600 hover:bg-purple-500
                    text-xs text-white transition"
                >
                  Test Backend
                </button>
              </div>
            </div>
            <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
              {debugInfo.slice(-5).map((log, i) => (
                <div key={i} className="text-purple-300 font-mono">
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Drag & Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !file && document.getElementById('file-input')?.click()}
          className={`
            relative border-2 border-dashed rounded-xl p-8 text-center
            transition-all cursor-pointer
            ${isDragging 
              ? 'border-cyan-400 bg-cyan-500/10' 
              : file
              ? 'border-green-500/50 bg-green-500/5'
              : 'border-white/20 hover:border-white/40 bg-white/5'
            }
          `}
        >
          <input
            id="file-input"
            type="file"
            accept="application/pdf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={isCheckingPages || isUploading}
          />

          <div className="space-y-4">
            {file ? (
              <>
                <CheckCircle className="w-12 h-12 mx-auto text-green-400" />
                <div>
                  <p className="text-white font-medium">{file.name}</p>
                  <p className="text-sm text-gray-400">
                    {formatFileSize(file.size)}
                    {pdfPageCount && ` • ${pdfPageCount} pages`}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveFile();
                  }}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md
                    text-xs text-gray-300 border border-white/20
                    hover:bg-white/5 transition"
                >
                  <X className="w-3 h-3" />
                  Remove
                </button>
              </>
            ) : (
              <>
                <Upload className="w-12 h-12 mx-auto text-gray-400" />
                <div>
                  <p className="text-white font-medium">
                    Drop your PDF here or click to browse
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    PDF only • Max 25MB • Up to 400 pages
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Translation Options */}
        {file && (
          <>
            {/* Direction */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Translation Direction
              </label>
              <select
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
                className="w-full bg-[#020617] border border-white/10
                  rounded-lg px-4 py-3 text-sm text-gray-200
                  focus:border-cyan-500 focus:outline-none transition"
              >
                <option value="to_en">Indian Language → English</option>
                <option value="from_en">English → Indian Language</option>
              </select>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {direction === "to_en" ? "Source Language" : "Target Language"}
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-[#020617] border border-white/10
                  rounded-lg px-4 py-3 text-sm text-gray-200
                  focus:border-cyan-500 focus:outline-none transition"
              >
                <option value="gu">Gujarati (ગુજરાતી)</option>
                <option value="hi">Hindi (हिन्दी)</option>
                <option value="mr">Marathi (मराठी)</option>
              </select>
            </div>

            {/* Mode */}
            {direction === "to_en" && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Translation Mode
                </label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                  className="w-full bg-[#020617] border border-white/10
                    rounded-lg px-4 py-3 text-sm text-gray-200
                    focus:border-cyan-500 focus:outline-none transition"
                >
                  <option value="general">General Translation</option>
                  <option value="government">Government / NCERT</option>
                </select>
                <p className="mt-2 text-xs text-gray-500">
                  {mode === "general"
                    ? "Best for everyday documents and personal content"
                    : "Optimized for official documents and textbooks"
                  }
                </p>
              </div>
            )}
          </>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
            <div className="flex items-start gap-2 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">Error</p>
                <p className="text-xs mt-1 opacity-90">{error}</p>
                {process.env.NODE_ENV === 'development' && (
                  <button
                    onClick={copyDebugInfo}
                    className="mt-2 text-xs underline hover:no-underline"
                  >
                    Copy debug info
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Upload Button */}
        {file && (
          <button
            onClick={handleUploadClick}
            disabled={isCheckingPages || isUploading || !sessionId}
            className="w-full py-3 rounded-lg font-medium text-white
              bg-gradient-to-r from-indigo-600 to-cyan-600
              hover:from-indigo-500 hover:to-cyan-500
              disabled:opacity-50 disabled:cursor-not-allowed
              transition shadow-lg flex items-center justify-center gap-2"
          >
            {isCheckingPages ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Checking pages...</span>
              </>
            ) : isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Uploading...</span>
              </>
            ) : !sessionId ? (
              <>
                <AlertCircle className="w-5 h-5" />
                <span>Session not ready</span>
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                <span>Upload & Translate</span>
              </>
            )}
          </button>
        )}

        {/* Privacy Note */}
        <p className="text-xs text-center text-gray-500">
          🔒 Your file is processed securely and automatically deleted after translation
        </p>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && paymentDetails && file && (
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => {
            setShowPaymentModal(false);
          }}
          onPaymentSuccess={handlePaymentSuccess}
          pageCount={paymentDetails.page_count}
          paymentAmount={paymentDetails.amount_inr}
          freePagesUsed={paymentDetails.free_pages}
          paidPages={paymentDetails.paid_pages}
          jobId={`temp_${Date.now()}`}
          initiatePayment={initiatePayment}
          isDemoMode={paymentConfig?.demo_mode}
        />
      )}
    </>
  );
}