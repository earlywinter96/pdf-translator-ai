import { useState, useEffect } from 'react';

interface RazorpaySuccessResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

interface RazorpayFailureResponse {
  error?: { description?: string };
}

interface RazorpayCheckout {
  open: () => void;
  on: (event: 'payment.failed', handler: (response: RazorpayFailureResponse) => void) => void;
}

interface RazorpayOrder {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  business_name: string;
  description: string;
  theme?: { color?: string };
  demo?: boolean;
}

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: RazorpaySuccessResponse) => void | Promise<void>;
  modal: { ondismiss: () => void };
  theme: { color: string };
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => RazorpayCheckout;
  }
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || 'https://pdf-translator-ai-ggqe.onrender.com';

async function reportPaymentEvent(jobId: string, event: string) {
  try {
    await fetch(`${API_BASE}/api/payment/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, event }),
    });
  } catch {
    // Funnel telemetry must never interrupt a customer's payment flow.
  }
}

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
  const [paymentConfig, setPaymentConfig] =
    useState<PaymentConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializePaymentSystem();
  }, []);

  const initializePaymentSystem = async () => {
    try {
      setIsLoading(true);
      await loadPaymentConfig();
      await initializeSession();
      setIsLoading(false);
    } catch (err: unknown) {
      setError(errorMessage(err, 'Failed to initialize payment system'));
      setIsLoading(false);
    }
  };

  // ===============================
  // SESSION MANAGEMENT
  // ===============================

  const initializeSession = async () => {
    try {
      let storedSessionId: string | null =
        localStorage.getItem('payment_session_id');

      if (!storedSessionId) {
        const response = await fetch(
          `${API_BASE}/api/payment/session/create`,
          { method: 'POST' }
        );

        if (!response.ok) {
          throw new Error('Failed to create session');
        }

        const data = await response.json();
        storedSessionId = data.session_id ?? null;

        if (storedSessionId) {
          localStorage.setItem(
            'payment_session_id',
            storedSessionId
          );
        }

        setFreePagesRemaining(data.free_pages_remaining);
      } else {
        const statusResponse = await fetch(
          `${API_BASE}/api/payment/session/${storedSessionId}/status`
        );

        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setFreePagesRemaining(statusData.free_pages_remaining);
        } else {
          localStorage.removeItem('payment_session_id');
          await initializeSession();
          return;
        }
      }

      setSessionId(storedSessionId);
    } catch (error) {
      throw error;
    }
  };

  const refreshSession = async () => {
    if (!sessionId) return;

    const response = await fetch(
      `${API_BASE}/api/payment/session/${sessionId}/status`
    );

    if (response.ok) {
      const data = await response.json();
      setFreePagesRemaining(data.free_pages_remaining);
    }
  };

  // ===============================
  // CONFIG
  // ===============================

  const loadPaymentConfig = async () => {
    const response = await fetch(
      `${API_BASE}/api/payment/config`
    );

    if (!response.ok) {
      throw new Error('Failed to load payment config');
    }

    const config = await response.json();
    setPaymentConfig(config);
  };

  // ===============================
  // PAYMENT CHECK
  // ===============================

  const checkPaymentRequired = async (
    pageCount: number
  ): Promise<PaymentCheck> => {
    if (!sessionId) {
      throw new Error('No session ID');
    }

    const response = await fetch(
      `${API_BASE}/api/payment/check-pages`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({ page_count: pageCount }),
      }
    );

    if (!response.ok) {
      throw new Error('Payment check failed');
    }

    return response.json();
  };

  // ===============================
  // PAYMENT INITIATION
  // ===============================

  const initiatePayment = async (
    jobId: string,
    pageCount: number
  ) => {
    if (!sessionId) {
      throw new Error('No session ID');
    }

    const orderResponse = await fetch(
      `${API_BASE}/api/payment/create-order`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({
          job_id: jobId,
          page_count: pageCount,
        }),
      }
    );

    if (!orderResponse.ok) {
      const err = await orderResponse.json().catch(() => ({}));
      throw new Error(err.detail || 'Order creation failed');
    }

    const orderData = await orderResponse.json() as RazorpayOrder;

    // Demo mode
    if (orderData.demo) {
      await refreshSession();
      return orderData.order_id;
    }

    // ✅ Razorpay TypeScript-safe usage
    const RazorpayConstructor = window.Razorpay;

    if (!RazorpayConstructor) {
      throw new Error('Razorpay SDK not loaded');
    }

    return new Promise<string | null>((resolve, reject) => {
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: orderData.business_name,
        description: orderData.description,
        order_id: orderData.order_id,

        handler: async (response: RazorpaySuccessResponse) => {
          try {
            const verifyResponse = await fetch(
              `${API_BASE}/api/payment/verify`,
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-Session-ID': sessionId,
                },
                body: JSON.stringify({
                  order_id: response.razorpay_order_id,
                  payment_id: response.razorpay_payment_id,
                  signature: response.razorpay_signature,
                  job_id: jobId,
                }),
              }
            );

            const verification = await verifyResponse.json().catch(() => null);
            if (verifyResponse.ok && verification?.verified) {
                await refreshSession();
                resolve(response.razorpay_order_id);
            } else {
              reject(new Error(verification?.detail || verification?.message || 'Payment verification failed'));
            }
          } catch (err) {
            reject(err);
          }
        },

        modal: {
          ondismiss: () => {
            void reportPaymentEvent(jobId, 'razorpay_dismissed');
            resolve(null);
          },
        },

        theme: {
          color: orderData.theme?.color || '#3399ff',
        },
      };

      const razorpay = new RazorpayConstructor(options);

      razorpay.on('payment.failed', (response: RazorpayFailureResponse) => {
        void reportPaymentEvent(jobId, 'payment_failed');
        reject(
          new Error(
            response?.error?.description || 'Payment failed'
          )
        );
      });

      void reportPaymentEvent(jobId, 'razorpay_opened');
      razorpay.open();
    });
  };

  return {
    sessionId,
    freePagesRemaining,
    paymentConfig,
    isLoading,
    error,
    checkPaymentRequired,
    initiatePayment,
    refreshSession,
    reportPaymentEvent,
  };
}
