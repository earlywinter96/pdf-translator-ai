"""Small, non-blocking Discord alert helper for operational events."""

import logging
import os
import ipaddress
import json
import asyncio
from io import BytesIO
from typing import Mapping

import httpx
import fitz

logger = logging.getLogger(__name__)
MAX_DISCORD_PREVIEW_BYTES = 8 * 1024 * 1024
_missing_webhook_warned = False


async def notify_discord(title: str, fields: Mapping[str, str | int]) -> None:
    """Send metadata-only events when a private webhook is configured."""
    global _missing_webhook_warned
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        if not _missing_webhook_warned:
            logger.error("Discord notifications disabled: DISCORD_WEBHOOK_URL is not configured")
            _missing_webhook_warned = True
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
            for attempt in range(2):
                response = await client.post(webhook_url, json=payload)
                if response.status_code != 429:
                    if response.is_error:
                        logger.error(
                            "Discord webhook rejected notification (%s): %s",
                            response.status_code, response.text[:300],
                        )
                    return
                retry_after = min(float(response.headers.get("retry-after", "2")), 10.0)
                logger.warning("Discord webhook rate limited; retrying in %.1fs", retry_after)
                if attempt == 0:
                    await asyncio.sleep(max(0.1, retry_after))
    except Exception as exc:
        # Notifications must never stop payments, uploads, or translations.
        logger.warning("Discord notification failed: %s", exc)


def _first_page_pdf_bytes(pdf_path: str) -> bytes:
    """Create a one-page PDF attachment without retaining another user file."""
    source = fitz.open(pdf_path)
    preview = fitz.open()
    try:
        preview.insert_pdf(source, from_page=0, to_page=0)
        return preview.tobytes(garbage=4, deflate=True)
    finally:
        preview.close()
        source.close()


async def notify_preview_documents(
    job_id: str,
    original_path: str,
    translated_path: str,
    page_count: int,
    paid_pages: int,
    amount_inr: float,
) -> None:
    """Attach the original and translated first pages to the private webhook."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.error("Discord preview notification skipped: DISCORD_WEBHOOK_URL is not configured")
        return

    fields: dict[str, str | int] = {
        "Job": job_id[:8],
        "Preview": "Original + translated first page attached",
        "Pages awaiting payment": paid_pages if paid_pages else "None — free document",
        "Full translation price": f"₹{amount_inr:.0f}" if paid_pages else "Free",
        "Status": "Preview ready — awaiting payment" if paid_pages else "Free first-page translation complete",
    }
    try:
        originals = _first_page_pdf_bytes(original_path)
        translated = _first_page_pdf_bytes(translated_path)
        files_to_send = [
            ("original-page-1.pdf", originals),
            ("translated-page-1.pdf", translated),
        ]
        too_large = [name for name, content in files_to_send if len(content) > MAX_DISCORD_PREVIEW_BYTES]
        if too_large:
            fields["Attachments"] = "Preview attachment too large to send"
            await notify_discord("LipiTranslate preview ready", fields)
            return

        payload = {"embeds": [{
            "title": "LipiTranslate preview ready",
            "color": 0x06B6D4,
            "fields": [
                {"name": str(name), "value": str(value)[:1024], "inline": True}
                for name, value in fields.items()
            ],
        }]}
        handles = []
        try:
            multipart_files = {}
            for index, (filename, content) in enumerate(files_to_send):
                handle = BytesIO(content)
                handles.append(handle)
                multipart_files[f"files[{index}]"] = (filename, handle, "application/pdf")
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    if attempt:
                        for handle in handles:
                            handle.seek(0)
                    response = await client.post(
                        webhook_url,
                        data={"payload_json": json.dumps(payload)},
                        files=multipart_files,
                    )
                    if response.status_code != 429:
                        response.raise_for_status()
                        break
                    retry_after = min(float(response.headers.get("retry-after", "2")), 10.0)
                    logger.warning("Discord preview webhook rate limited; retrying in %.1fs", retry_after)
                    if attempt == 0:
                        await asyncio.sleep(max(0.1, retry_after))
        finally:
            for handle in handles:
                handle.close()
    except Exception as exc:
        logger.warning("Discord preview notification failed: %s", exc)


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
    paid_pages: int,
    billable_characters: int,
    amount_inr: float,
    client_ip: str | None,
    pricing_basis: str = "detected",
    available_packages: list[dict] | None = None,
) -> None:
    """Send an upload alert with filename and approximate IP-derived location."""
    location = await get_approximate_location(client_ip)
    offers = available_packages or []
    offer_summary = ", ".join(
        f"{item.get('page_limit')}p ₹{float(item.get('amount_inr', 0)):.0f}"
        for item in offers
    ) or (f"Full PDF ₹{amount_inr:.0f}" if payment_required else "Free")
    size_flag = " — LARGE DOCUMENT" if page_count >= 100 else (" — 20+ pages" if page_count >= 20 else "")
    await notify_discord(f"LipiTranslate PDF upload{size_flag}", {
        "File": filename or "Unnamed PDF",
        "Pages": page_count,
        "Direction": f"{source_language} -> {target_language}",
        "Approx. location": location,
        "Pricing input": (
            f"{billable_characters:,} detected characters"
            if pricing_basis == "detected" else
            f"{billable_characters:,} estimated scan characters (locked pages not OCR-read)"
            if pricing_basis == "scan_estimate" else "Per-page price"
        ),
        "Full translation price": f"₹{amount_inr:.0f}" if payment_required else "Free",
        "Offers shown": offer_summary,
        "Document size": f"{page_count} pages / {billable_characters:,} chars",
        "Status": (
            f"1-page free preview started; {paid_pages} page(s) await payment"
            if payment_required else "Free preview started"
        ),
    })
