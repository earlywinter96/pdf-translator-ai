"use client";

import { useEffect } from "react";
import { CheckCircle } from "lucide-react";

export default function PaymentSuccessPage() {
  useEffect(() => {
    const timer = window.setTimeout(() => window.location.replace("/convert"), 3500);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className="flex min-h-[70vh] items-center justify-center px-6 text-center">
      <div className="max-w-lg rounded-2xl border border-emerald-400/40 bg-slate-900 p-8">
        <CheckCircle className="mx-auto h-14 w-14 text-emerald-400" />
        <h1 className="mt-4 text-2xl font-bold text-white">Payment received</h1>
        <p className="mt-2 text-cyan-200">LipiTranslate.in is preparing your translated PDF.</p>
        <p className="mt-3 text-sm text-gray-300">Returning to the translation page…</p>
      </div>
    </main>
  );
}
