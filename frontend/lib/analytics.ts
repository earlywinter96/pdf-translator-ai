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

/** Report a client-side failure to the backend error channel.
 *  The payload is deliberately short and excludes file contents or PII.
 */
export function reportSiteError(error: unknown, context?: string) {
  const message = error instanceof Error ? error.message : String(error ?? "Unknown client error");
  void fetch(`${API_BASE}/api/analytics/error`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      error: message.slice(0, 300),
      context: context?.slice(0, 120) || "client",
      page: typeof window === "undefined" ? "unknown" : window.location.pathname,
    }),
    keepalive: true,
  }).catch(() => undefined);
}
