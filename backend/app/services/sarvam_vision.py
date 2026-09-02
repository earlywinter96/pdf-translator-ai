"""Sarvam Vision OCR for scanned PDFs.

This is deliberately an opt-in server feature.  It only runs when a document
has no usable selectable-text layer and ``SARVAM_VISION_ENABLED=true`` is set;
digital PDFs continue through the faster, no-extra-cost layout path.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import fitz
import requests

from app.services.layout_pdf_writer import TextBlock

logger = logging.getLogger(__name__)

VISION_LANGUAGE_CODES = {
    "english": "en-IN", "hindi": "hi-IN", "marathi": "mr-IN", "gujarati": "gu-IN",
    "tamil": "ta-IN", "telugu": "te-IN", "kannada": "kn-IN", "malayalam": "ml-IN",
    "bengali": "bn-IN", "punjabi": "pa-IN", "en": "en-IN", "hi": "hi-IN",
    "mr": "mr-IN", "gu": "gu-IN", "ta": "ta-IN", "te": "te-IN",
}
TERMINAL_STATES = {"completed", "partially_completed", "failed", "rejected"}


def is_sarvam_vision_enabled() -> bool:
    return os.getenv("SARVAM_VISION_ENABLED", "false").lower() in {"1", "true", "yes"}


def _value(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _plain(value: Any) -> Any:
    """Convert SDK response models to ordinary JSON-compatible objects."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _bbox_to_rect(bbox: Any, page: fitz.Page, source_width: float, source_height: float) -> tuple[float, float, float, float] | None:
    """Turn Vision JSON bounding-box variants into PDF points."""
    if isinstance(bbox, dict):
        left = bbox.get("x", bbox.get("left", bbox.get("x0")))
        top = bbox.get("y", bbox.get("top", bbox.get("y0")))
        right = bbox.get("right", bbox.get("x1"))
        bottom = bbox.get("bottom", bbox.get("y1"))
        if right is None and left is not None:
            right = left + bbox.get("width", 0)
        if bottom is None and top is not None:
            bottom = top + bbox.get("height", 0)
    elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        left, top, right, bottom = bbox[:4]
    else:
        return None
    try:
        left, top, right, bottom = map(float, (left, top, right, bottom))
    except (TypeError, ValueError):
        return None
    if right <= left or bottom <= top:
        return None
    # Document AI returns page dimensions alongside JSON blocks. Scaling also
    # works for pixels and avoids assuming A4 on uploaded documents.
    scale_x = page.rect.width / source_width if source_width else 1
    scale_y = page.rect.height / source_height if source_height else 1
    return (left * scale_x, top * scale_y, right * scale_x, bottom * scale_y)


def _blocks_from_metadata(metadata: dict[str, Any], page: fitz.Page, page_number: int) -> list[TextBlock]:
    # Document AI JSON has used both a direct page object and a result/page
    # wrapper across SDK releases. Normalise both before reading blocks.
    metadata = metadata.get("page", metadata.get("result", metadata))
    dimensions = metadata.get("dimensions", {})
    width = float(metadata.get("width") or dimensions.get("width") or page.rect.width)
    height = float(metadata.get("height") or dimensions.get("height") or page.rect.height)
    block_container = metadata.get("layout", metadata)
    result: list[TextBlock] = []
    for item in block_container.get("blocks", []):
        text = str(item.get("text") or "").strip()
        rect = _bbox_to_rect(item.get("bbox"), page, width, height)
        if not text or not rect:
            continue
        rect_height = rect[3] - rect[1]
        result.append(TextBlock(
            page_number=page_number,
            rect=rect,
            text=text,
            font_size=max(8.0, min(24.0, rect_height * 0.82)),
            color=(0, 0, 0),
            is_bold=str(item.get("type", "")).lower() in {"title", "heading", "header"},
        ))
    return result


def _page_payloads(payload: Any) -> list[dict[str, Any]]:
    """Find Document AI page JSON in SDK responses or downloaded metadata."""
    payload = _plain(payload)
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("pages"), list):
        return [page for page in payload["pages"] if isinstance(page, dict)]
    if isinstance(payload.get("result"), dict):
        return _page_payloads(payload["result"])
    if isinstance(payload.get("page"), dict):
        return [payload]
    if isinstance(payload.get("blocks"), list) or isinstance(payload.get("layout"), dict):
        return [payload]
    return []


def _vision_blocks_sync(pdf_path: str, source_language: str, max_pages: int | None) -> list[TextBlock]:
    """Submit at most ten pages per Vision job and return positioned blocks."""
    if not is_sarvam_vision_enabled() or not os.getenv("SARVAM_API_KEY"):
        return []
    try:
        from sarvamai import SarvamAI
    except ImportError:
        logger.error("Sarvam Vision is enabled but the sarvamai package is missing")
        return []

    document = fitz.open(pdf_path)
    try:
        requested_pages = min(document.page_count, max_pages) if max_pages else document.page_count
        client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"], timeout=90.0)
        all_blocks: list[TextBlock] = []
        language = VISION_LANGUAGE_CODES.get(source_language.lower(), "en-IN")
        for start in range(0, requested_pages, 10):
            end = min(start + 10, requested_pages)
            partial = fitz.open()
            partial.insert_pdf(document, from_page=start, to_page=end - 1)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
                temp_path = temp.name
                partial.save(temp_path, garbage=4, deflate=True)
            partial.close()
            try:
                with open(temp_path, "rb") as pdf_file:
                    job = client.doc_ai.digitise(
                        file=[(Path(pdf_path).name, pdf_file, "application/pdf")],
                        language=language,
                        output_format="json",
                    )
                job_id = _value(job, "job_id")
                deadline = time.monotonic() + 180
                while time.monotonic() < deadline:
                    status = client.doc_ai.get_status(job_id=job_id)
                    state = str(_value(status, "status", "")).lower()
                    if state in TERMINAL_STATES:
                        break
                    time.sleep(3)
                if state not in {"completed", "partially_completed"}:
                    logger.warning("Sarvam Vision job %s ended as %s", job_id, state)
                    continue
                # Current Document AI exposes structured result pages directly
                # through the SDK. Prefer that path; it avoids depending on a
                # ZIP filename convention and provides the exact Vision boxes.
                payloads: list[dict[str, Any]] = []
                try:
                    payloads = _page_payloads(client.doc_ai.get_results(job_id=job_id))
                except Exception as results_error:
                    logger.info("Sarvam Vision results endpoint unavailable for %s: %s", job_id, results_error)
                if not payloads:
                    download = client.doc_ai.get_download_url(job_id=job_id)
                    response = requests.get(_value(download, "url"), timeout=60)
                    response.raise_for_status()
                    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                        metadata_names = sorted(
                            name for name in archive.namelist()
                            if name.endswith(".json") and "page_" in name
                        )
                        import json
                        payloads = [json.loads(archive.read(name)) for name in metadata_names]
                        if not payloads:
                            logger.warning("Sarvam Vision returned no page metadata for job %s (files: %s)", job_id, archive.namelist())
                batch_blocks = []
                for offset, metadata in enumerate(payloads):
                    if start + offset < document.page_count:
                        batch_blocks.extend(_blocks_from_metadata(metadata, document[start + offset], start + offset))
                logger.info("Sarvam Vision job %s produced %s positioned blocks for pages %s-%s", job_id, len(batch_blocks), start + 1, end)
                all_blocks.extend(batch_blocks)
            except Exception as exc:
                logger.warning("Sarvam Vision OCR failed for pages %s-%s: %s", start + 1, end, exc)
            finally:
                os.unlink(temp_path)
        return all_blocks
    finally:
        document.close()


async def extract_sarvam_vision_blocks(
    pdf_path: str, source_language: str, max_pages: int | None = None
) -> list[TextBlock]:
    """Non-blocking async wrapper for Sarvam Vision's asynchronous job API."""
    return await asyncio.to_thread(_vision_blocks_sync, pdf_path, source_language, max_pages)
