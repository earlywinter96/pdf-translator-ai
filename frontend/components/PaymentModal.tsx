// components/PaymentModal.tsx
/**
 * Payment Modal Component
 * Shows payment details and initiates Razorpay checkout
 */

"use client";

import { useState } from 'react';
import { X, CreditCard, AlertCircle, CheckCircle } from 'lucide-react';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCancel: () => void;
  onPaymentSuccess: (orderId: string) => void | Promise<void>;
  pageCount: number;
  paymentAmount: number;
  freePagesUsed: number;
  paidPages: number;
  jobId: string;
  initiatePayment: (jobId: string, pageCount: number) => Promise<string | null>;
  isDemoMode?: boolean;
}

export default function PaymentModal({
  isOpen,
  onClose,
  onCancel,
  onPaymentSuccess,
  pageCount,
  paymentAmount,
  freePagesUsed,
  paidPages,
  jobId,
  initiatePayment,
  isDemoMode = false,
}: PaymentModalProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handlePayment = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      const orderId = await initiatePayment(jobId, pageCount);
      
      if (orderId) {
        await onPaymentSuccess(orderId);
        onClose();
      } else {
        setError('Payment failed or was cancelled');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl max-w-md w-full border border-white/10 shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-semibold text-white">Unlock Remaining Pages</h2>
          <button
            onClick={onCancel}
            disabled={isProcessing}
            className="text-gray-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          
          {/* Demo Mode Warning */}
          {isDemoMode && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-200">
                  <p className="font-medium mb-1">Demo Mode Active</p>
                  <p className="text-yellow-300/80">
                    This is a test payment. No real money will be charged.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Payment Breakdown */}
          <div className="bg-white/5 rounded-lg p-4 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Total Pages</span>
              <span className="text-white font-medium">{pageCount} pages</span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Free Preview</span>
              <span className="text-green-400 font-medium">
                {freePagesUsed} page{freePagesUsed === 1 ? "" : "s"} (already translated)
              </span>
            </div>
            
            <div className="h-px bg-white/10" />
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Paid Pages</span>
              <span className="text-white font-medium">{paidPages} pages</span>
            </div>
            
            <div className="h-px bg-white/10" />
            
            <div className="flex justify-between">
              <span className="text-white font-medium">Total Amount</span>
              <span className="text-2xl font-bold text-cyan-400">
                ₹{paymentAmount.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>Secure payment via Razorpay</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>Only the remaining pages are translated after payment</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span>Files auto-deleted after download</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Payment Button */}
          <button
            onClick={handlePayment}
            disabled={isProcessing}
            className="w-full py-3 rounded-lg font-medium text-white
              bg-gradient-to-r from-indigo-600 to-cyan-600
              hover:from-indigo-500 hover:to-cyan-500
              disabled:opacity-50 disabled:cursor-not-allowed
              transition shadow-lg flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <CreditCard className="w-5 h-5" />
                <span>Proceed to Payment</span>
              </>
            )}
          </button>

          {/* Cancel Button */}
          <button
            onClick={onCancel}
            disabled={isProcessing}
            className="w-full py-2 text-sm text-gray-400 hover:text-white transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
