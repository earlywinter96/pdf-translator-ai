"""Small, non-blocking Discord alert helper for operational events."""

import logging
import os
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
