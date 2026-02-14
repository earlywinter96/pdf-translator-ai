import { useState, useEffect } from 'react';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

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
    } catch (err: any) {
      setError(err?.message || 'Failed to initialize payment system');
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

    const orderData = await orderResponse.json();

    // Demo mode
    if (orderData.demo) {
      await refreshSession();
      return orderData.order_id;
    }

    // ✅ Razorpay TypeScript-safe usage
    const RazorpayConstructor = (window as any).Razorpay;

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

        handler: async function (response: any) {
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

            if (verifyResponse.ok) {
              await refreshSession();
              resolve(response.razorpay_order_id);
            } else {
              reject(new Error('Payment verification failed'));
            }
          } catch (err) {
            reject(err);
          }
        },

        modal: {
          ondismiss: () => resolve(null),
        },

        theme: {
          color: orderData.theme?.color || '#3399ff',
        },
      };

      const razorpay = new RazorpayConstructor(options);

      razorpay.on('payment.failed', (response: any) => {
        reject(
          new Error(
            response?.error?.description || 'Payment failed'
          )
        );
      });

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
  };
}
