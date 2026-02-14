/**
 * Payment Hook - usePayment (CORRECTED)
 * ====================================
 * FIXED: Corrected fetch() syntax error on line 138
 */

import { useState, useEffect } from 'react';

// API base URL from environment
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface PaymentConfig {
  key_id: string;
  demo_mode: boolean;
  free_pages_limit: number;
  currency: string;
  currency_symbol: string;
}

interface PaymentCheck {
  requires_payment: boolean;
  free_pages: number;
  paid_pages: number;
  amount: number;
  amount_inr: number;
  message: string;
  can_proceed: boolean;
}

export function usePayment() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [freePagesRemaining, setFreePagesRemaining] = useState(10);
  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  useEffect(() => {
    initializePaymentSystem();
  }, []);

  const initializePaymentSystem = async () => {
    try {
      setIsLoading(true);
      
      // Step 1: Load payment config
      await loadPaymentConfig();
      
      // Step 2: Initialize or restore session
      await initializeSession();
      
      setIsLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize payment system');
      setIsLoading(false);
    }
  };

  // ============================================================================
  // SESSION MANAGEMENT
  // ============================================================================

  const initializeSession = async () => {
    try {
      let storedSessionId = localStorage.getItem('payment_session_id');
      
      if (!storedSessionId) {
        console.log('🔐 Creating new payment session...');
        const response = await fetch(`${API_BASE}/api/payment/session/create`, {
          method: 'POST',
        });
        
        if (!response.ok) {
          throw new Error('Failed to create session');
        }
        
        const data = await response.json();
        storedSessionId = data.session_id;
        
        localStorage.setItem('payment_session_id', storedSessionId);
        
        console.log('✅ Session created:', storedSessionId);
        setFreePagesRemaining(data.free_pages_remaining);
      } else {
        console.log('🔄 Restoring existing session:', storedSessionId);
        
        const statusResponse = await fetch(
          `${API_BASE}/api/payment/session/${storedSessionId}/status`
        );
        
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setFreePagesRemaining(statusData.free_pages_remaining);
          console.log('✅ Session restored - Free pages:', statusData.free_pages_remaining);
        } else {
          console.log('⚠️ Session invalid - creating new one');
          localStorage.removeItem('payment_session_id');
          await initializeSession();
          return;
        }
      }
      
      setSessionId(storedSessionId);
    } catch (error) {
      console.error('❌ Session initialization failed:', error);
      throw error;
    }
  };

  const refreshSession = async () => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(
        `${API_BASE}/api/payment/session/${sessionId}/status`
      );
      
      if (response.ok) {
        const data = await response.json();
        setFreePagesRemaining(data.free_pages_remaining);
        console.log('🔄 Session refreshed - Free pages:', data.free_pages_remaining);
      }
    } catch (error) {
      console.error('Failed to refresh session:', error);
    }
  };

  // ============================================================================
  // PAYMENT CONFIG - ✅ FIXED (Line 138 corrected)
  // ============================================================================

  const loadPaymentConfig = async () => {
    try {
      // ✅ FIXED: Changed backtick to opening parenthesis
      const response = await fetch(`${API_BASE}/api/payment/config`);
      
      if (!response.ok) {
        throw new Error('Failed to load payment config');
      }
      
      const config = await response.json();
      setPaymentConfig(config);
      
      console.log('💳 Payment config loaded:', {
        demo_mode: config.demo_mode,
        free_pages: config.free_pages_limit,
      });
    } catch (error) {
      console.error('❌ Failed to load payment config:', error);
      throw error;
    }
  };

  // ============================================================================
  // PAYMENT CALCULATION
  // ============================================================================

  const checkPaymentRequired = async (pageCount: number): Promise<PaymentCheck> => {
    if (!sessionId) {
      throw new Error('No session ID - payment system not initialized');
    }

    try {
      const response = await fetch(`${API_BASE}/api/payment/check-pages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({ page_count: pageCount }),
      });

      if (!response.ok) {
        throw new Error('Payment check failed');
      }

      const data = await response.json();
      
      console.log('📊 Payment check:', {
        pages: pageCount,
        requires_payment: data.requires_payment,
        amount: `₹${data.amount_inr}`,
      });

      return data;
    } catch (error: any) {
      console.error('❌ Payment check failed:', error);
      throw error;
    }
  };

  // ============================================================================
  // PAYMENT INITIATION
  // ============================================================================

  const initiatePayment = async (
    jobId: string,
    pageCount: number
  ) => {
    if (!sessionId) {
      throw new Error('No session ID - payment system not initialized');
    }

    try {
      console.log('💳 Creating payment order...');
      
      const orderResponse = await fetch(`${API_BASE}/api/payment/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({
          job_id: jobId,
          page_count: pageCount,
        }),
      });

      if (!orderResponse.ok) {
        const errorData = await orderResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Order creation failed');
      }

      const orderData = await orderResponse.json();
      
      console.log('✅ Order created:', orderData.order_id);

      // Demo mode
      if (orderData.demo) {
        console.log('🎭 Demo mode - auto-verifying payment');
        
        const verifyResponse = await fetch(`${API_BASE}/api/payment/verify`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': sessionId,
          },
          body: JSON.stringify({
            order_id: orderData.order_id,
            payment_id: 'demo_payment',
            signature: 'demo_signature',
            job_id: jobId,
          }),
        });

        if (verifyResponse.ok) {
          console.log('✅ Demo payment verified');
          await refreshSession();
          return orderData.order_id;
        } else {
          throw new Error('Demo payment verification failed');
        }
      }

      // Production mode - Razorpay
      console.log('🚀 Opening Razorpay checkout...');
      
      return new Promise<string | null>((resolve, reject) => {
        if (typeof window.Razorpay === 'undefined') {
          reject(new Error('Razorpay SDK not loaded'));
          return;
        }

        const options = {
          key: orderData.key_id,
          amount: orderData.amount,
          currency: orderData.currency,
          name: orderData.business_name,
          description: orderData.description,
          order_id: orderData.order_id,
          
          handler: async function (response: any) {
            try {
              console.log('✅ Payment successful, verifying...');
              
              const verifyResponse = await fetch(`${API_BASE}/api/payment/verify`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-Session-ID': sessionId!,
                },
                body: JSON.stringify({
                  order_id: response.razorpay_order_id,
                  payment_id: response.razorpay_payment_id,
                  signature: response.razorpay_signature,
                  job_id: jobId,
                }),
              });

              if (verifyResponse.ok) {
                console.log('✅ Payment verified successfully');
                await refreshSession();
                resolve(response.razorpay_order_id);
              } else {
                const errorData = await verifyResponse.json().catch(() => ({}));
                throw new Error(errorData.message || 'Payment verification failed');
              }
            } catch (error: any) {
              console.error('❌ Payment verification error:', error);
              reject(error);
            }
          },

          modal: {
            ondismiss: function () {
              console.log('⚠️ Payment modal closed by user');
              resolve(null);
            },
          },

          theme: {
            color: orderData.theme?.color || '#3399ff',
          },

          prefill: orderData.prefill || {},
        };

        const razorpay = new window.Razorpay(options);
        
        razorpay.on('payment.failed', function (response: any) {
          console.error('❌ Payment failed:', response.error);
          reject(new Error(response.error.description || 'Payment failed'));
        });

        razorpay.open();
      });
    } catch (error: any) {
      console.error('❌ Payment initiation failed:', error);
      throw error;
    }
  };

  // ============================================================================
  // RETURN HOOK INTERFACE
  // ============================================================================

  return {
    sessionId,
    freePagesRemaining,
    paymentConfig,
    isLoading,
    error,
    checkPaymentRequired,
    initiatePayment,
    refreshSession,
  };
}