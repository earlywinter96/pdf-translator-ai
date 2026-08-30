"use client";

import { useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai-ggqe.onrender.com";
const VISIT_KEY = "lipitranslate_discord_visit_date";

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
