"use client";

import { useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://lipitranslate-api-500686400179.us-central1.run.app";
const VISIT_KEY = "lipitranslate_telegram_visit_date_v2";

/** Notify operations once per browser per day, without sending personal data. */
export default function VisitTracker() {
  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    if (localStorage.getItem(VISIT_KEY) === today) return;

    fetch(`${API_BASE}/api/analytics/visit`, { method: "POST" })
      .then((response) => {
        if (response.ok) localStorage.setItem(VISIT_KEY, today);
      })
      .catch(() => undefined);
  }, []);

  return null;
}
