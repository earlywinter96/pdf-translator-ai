"""Layout-preserving PDF writer.

For text-based PDFs, PyMuPDF gives us the location of every selectable text
block.  We retain the source page as the canvas, remove only those text
objects, and insert Sarvam's translation into the same rectangles.  Images,
backgrounds, lines, tables, and other page artwork therefore stay intact.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, List

import fitz

from app.services.pdf_writer import FONTS_DIR, get_language_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextBlock:
    """A selectable text block and the visual information needed to replace it."""

    page_number: int
    rect: tuple[float, float, float, float]
    text: str
    font_size: float
    color: tuple[float, float, float]
    is_bold: bool


def _pdf_color_to_rgb(color: int) -> tuple[float, float, float]:
    return (
        ((color >> 16) & 255) / 255,
        ((color >> 8) & 255) / 255,
        (color & 255) / 255,
    )


def extract_text_blocks(pdf_path: str) -> List[TextBlock]:
    """Extract non-empty selectable text blocks in display order.

    This intentionally only supports digital PDFs.  An image-only/scanned PDF
    has no reliable text geometry, so callers can use the normal OCR fallback.
    """
    document = fitz.open(pdf_path)
    blocks: List[TextBlock] = []
    try:
        for page_number, page in enumerate(document):
            for block in page.get_text("dict", sort=True).get("blocks", []):
                if block.get("type") != 0:
                    continue
                text = "\n".join(
                    "".join(span.get("text", "") for span in line.get("spans", []))
                    for line in block.get("lines", [])
                ).strip()
                if not text:
                    continue
                first_span = next(
                    (
                        span
                        for line in block.get("lines", [])
                        for span in line.get("spans", [])
                        if span.get("text", "").strip()
                    ),
                    None,
                )
                if first_span is None:
                    continue
                blocks.append(
                    TextBlock(
                        page_number=page_number,
                        rect=tuple(block["bbox"]),
                        text=text,
                        font_size=float(first_span.get("size", 11)),
                        color=_pdf_color_to_rgb(int(first_span.get("color", 0))),
                        is_bold=bool(int(first_span.get("flags", 0)) & 16),
                    )
                )
    finally:
        document.close()
    return blocks


def has_usable_layout(blocks: Iterable[TextBlock]) -> bool:
    """Return true only when source text has enough geometry to preserve."""
    return sum(len(block.text) for block in blocks) >= 40


def _font_path(target_language: str, is_bold: bool) -> str | None:
    font_name = get_language_config(target_language)["font"]
    bundled_fonts = {
        "NotoSans": "NotoSans-Bold.ttf" if is_bold else "NotoSans-Regular.ttf",
        "NotoSansDevanagari": "NotoSansDevanagari-Bold.ttf" if is_bold else "NotoSansDevanagari-Regular.ttf",
        "NotoSansGujarati": "NotoSansGujarati-Bold.ttf" if is_bold else "NotoSansGujarati-Regular.ttf",
    }
    filename = bundled_fonts.get(font_name)
    return os.path.join(FONTS_DIR, filename) if filename else None


def _fit_font_size(rect: fitz.Rect, original_size: float, text: str) -> float:
    """Use a sensible starting size and leave room for longer Indic text."""
    # Very small rectangles are commonly labels in tables.  Avoid a size that
    # looks oversized when a translation expands slightly.
    if rect.height < original_size * 1.35:
        return max(5.5, min(original_size, rect.height * 0.72))
    return max(6.0, original_size * 0.95)


def create_layout_preserved_pdf(
    source_pdf_path: str,
    blocks: List[TextBlock],
    translated_blocks: List[str],
    output_path: str,
    target_language: str,
    page_limit: int | None = None,
) -> dict:
    """Write a translated PDF that retains the original visual design.

    Untranslated or too-short blocks are deliberately not redacted; numbers,
    names, and short labels remain visible rather than disappearing.
    """
    if len(blocks) != len(translated_blocks):
        raise ValueError("Each layout block must have exactly one translation")

    document = fitz.open(source_pdf_path)
    replaced = 0
    overflowed = 0
    try:
        if page_limit is not None and document.page_count > page_limit:
            document.delete_pages(page_limit, document.page_count - 1)

        for page in document:
            regular_font = _font_path(target_language, False)
            bold_font = _font_path(target_language, True)
            if regular_font:
                page.insert_font(fontname="LipiTranslateRegular", fontfile=regular_font)
                page.insert_font(fontname="LipiTranslateBold", fontfile=bold_font)

        # Redact text only. Images and vector graphics are explicitly ignored,
        # which keeps CV photographs, coloured backgrounds and table lines.
        for block, translation in zip(blocks, translated_blocks):
            if not translation or translation.strip() == block.text.strip():
                continue
            rect = fitz.Rect(block.rect)
            document[block.page_number].add_redact_annot(rect, fill=False, cross_out=False)

        for page in document:
            page.apply_redactions(images=0, graphics=0, text=0)

        for block, translation in zip(blocks, translated_blocks):
            translation = " ".join(translation.split())
            if not translation or translation == block.text.strip():
                continue
            page = document[block.page_number]
            font_path = _font_path(target_language, block.is_bold)
            font_name = "LipiTranslateBold" if block.is_bold else "LipiTranslateRegular"
            rect = fitz.Rect(block.rect)
            # A small inset stops glyphs touching original table borders.
            rect += (1, 0.5, -1, -0.5)
            size = _fit_font_size(rect, block.font_size, translation)
            result = page.insert_textbox(
                rect,
                translation,
                fontname=font_name if font_path else ("hebo" if block.is_bold else "helv"),
                fontfile=font_path,
                fontsize=size,
                color=block.color,
                lineheight=1.05,
                overlay=True,
            )
            if result < 0:
                # Retry smaller before accepting a visibly clipped block.
                result = page.insert_textbox(
                    rect,
                    translation,
                    fontname=font_name if font_path else ("hebo" if block.is_bold else "helv"),
                    fontfile=font_path,
                    fontsize=max(5.0, size * 0.72),
                    color=block.color,
                    lineheight=1.0,
                    overlay=True,
                )
            if result < 0:
                overflowed += 1
                logger.warning("Translation did not fit text block on page %s: %s", block.page_number + 1, translation[:80])
            else:
                replaced += 1

        document.set_metadata({**document.metadata, "producer": "LipiTranslate - layout preserved"})
        document.save(output_path, garbage=4, deflate=True)
    finally:
        document.close()

    return {"replaced_blocks": replaced, "overflowed_blocks": overflowed}


def append_payment_required_page(output_path: str, total_pages: int) -> None:
    """Append a clear lock screen without sending more text to Sarvam."""
    document = fitz.open(output_path)
    try:
        reference = document[0].rect if document.page_count else fitz.paper_rect("a4")
        page = document.new_page(width=reference.width, height=reference.height)
        page.draw_rect(page.rect, color=None, fill=(0.02, 0.09, 0.16), overlay=False)
        panel = fitz.Rect(48, reference.height * 0.24, reference.width - 48, reference.height * 0.70)
        page.draw_rect(panel, color=(0.1, 0.75, 0.85), fill=(0.04, 0.16, 0.24), width=1.2)
        page.insert_textbox(
            fitz.Rect(panel.x0 + 30, panel.y0 + 42, panel.x1 - 30, panel.y0 + 105),
            "Payment required for the remaining pages",
            fontname="hebo", fontsize=21, color=(1, 1, 1), align=1,
        )
        page.insert_textbox(
            fitz.Rect(panel.x0 + 44, panel.y0 + 125, panel.x1 - 44, panel.y0 + 230),
            f"This document has {total_pages} pages. You received a translated first-page preview; the remaining pages are locked.",
            fontname="helv", fontsize=12, color=(0.82, 0.88, 0.92), align=1, lineheight=1.4,
        )
        page.insert_textbox(
            fitz.Rect(panel.x0 + 44, panel.y0 + 250, panel.x1 - 44, panel.y0 + 310),
            "Full-document translation will be available after payment is enabled.",
            fontname="hebo", fontsize=13, color=(0.3, 0.88, 0.92), align=1,
        )
        document.save(output_path + ".preview", garbage=4, deflate=True)
    finally:
        document.close()
    os.replace(output_path + ".preview", output_path)
