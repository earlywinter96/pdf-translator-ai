"""Small, non-blocking Discord alert helper for operational events."""

import logging
import os
import ipaddress
from typing import Mapping

import httpx

logger = logging.getLogger(__name__)


async def notify_discord(title: str, fields: Mapping[str, str | int]) -> None:
    """Send metadata-only events when a private webhook is configured."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    payload = {
        "embeds": [{
            "title": title,
            "color": 0x06B6D4,
            "fields": [
                {"name": str(name), "value": str(value)[:1024], "inline": True}
                for name, value in fields.items()
            ],
        }]
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
    except Exception as exc:
        # Notifications must never stop payments, uploads, or translations.
        logger.warning("Discord notification failed: %s", exc)


async def get_approximate_location(client_ip: str | None) -> str:
    """Return country and region only; never retain or send the visitor IP."""
    if not client_ip:
        return "Unavailable"

    try:
        if not ipaddress.ip_address(client_ip).is_global:
            return "Unavailable"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"https://ipwho.is/{client_ip}")
            response.raise_for_status()
            data = response.json()
        if not data.get("success", True):
            return "Unavailable"
        parts = [data.get("region"), data.get("country")]
        return ", ".join(str(part) for part in parts if part) or "Unavailable"
    except Exception as exc:
        logger.info("Approximate upload location unavailable: %s", exc)
        return "Unavailable"


async def notify_pdf_upload(
    filename: str | None,
    page_count: int,
    source_language: str,
    target_language: str,
    payment_required: bool,
    client_ip: str | None,
) -> None:
    """Send an upload alert with filename and approximate IP-derived location."""
    location = await get_approximate_location(client_ip)
    await notify_discord("LipiTranslate PDF upload", {
        "File": filename or "Unnamed PDF",
        "Pages": page_count,
        "Direction": f"{source_language} -> {target_language}",
        "Approx. location": location,
        "Status": "Payment required" if payment_required else "Free preview started",
    })
