const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai-ggqe.onrender.com";

/** Best-effort, privacy-safe interaction telemetry for the private Discord log. */
export function trackSiteInteraction(event: string) {
  void fetch(`${API_BASE}/api/analytics/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event, page: window.location.pathname }),
    keepalive: true,
  }).catch(() => undefined);
}
