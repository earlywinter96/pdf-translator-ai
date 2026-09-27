const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://lipitranslate-api-500686400179.us-central1.run.app";

/** Best-effort, privacy-safe interaction telemetry for the private Discord log. */
export function trackSiteInteraction(event: string, metadata?: { jobId?: string }) {
  const payload = JSON.stringify({
    event,
    page: typeof window === "undefined" ? "unknown" : window.location.pathname,
    job_id: metadata?.jobId,
  });
  // sendBeacon is designed for tab closes/new-tab navigation and is much
  // less likely than fetch(keepalive) to lose the preview/download event.
  if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
    try {
      const accepted = navigator.sendBeacon(
        `${API_BASE}/api/analytics/event`,
        new Blob([payload], { type: "application/json" }),
      );
      if (accepted) return;
    } catch {
      // Fall through to keepalive fetch for browsers that reject cross-origin
      // Beacon requests.
    }
  }
  void fetch(`${API_BASE}/api/analytics/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
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
