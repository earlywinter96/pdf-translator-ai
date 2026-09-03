"""Layout-preserving PDF writer.

For text-based PDFs, PyMuPDF gives us the location of every selectable text
block.  We retain the source page as the canvas, remove only those text
objects, and insert Sarvam's translation into the same rectangles.  Images,
backgrounds, lines, tables, and other page artwork therefore stay intact.
"""

from __future__ import annotations

import logging
import os
import re
from html import unescape
from dataclasses import dataclass
from typing import Iterable, List

import fitz
import pytesseract
from pdf2image import convert_from_path

from app.services.pdf_writer import FONTS_DIR, get_language_config
from app.services.pdf_reader import TESSERACT_LANG_MAP, prepare_image_for_ocr

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
    """Extract non-empty selectable text fragments in display order.

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
                # A worksheet often keeps two answer choices in one PDF
                # block. Redrawing that whole block after translation makes it
                # spill across columns. Use each positioned span as a text box
                # so the original column and answer-key geometry is retained.
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        blocks.append(
                            TextBlock(
                                page_number=page_number,
                                rect=tuple(span["bbox"]),
                                text=text,
                                font_size=float(span.get("size", 11)),
                                color=_pdf_color_to_rgb(int(span.get("color", 0))),
                                is_bold=bool(int(span.get("flags", 0)) & 16),
                            )
                        )
    finally:
        document.close()
    return blocks


def has_usable_layout(blocks: Iterable[TextBlock]) -> bool:
    """Return true only when source text has enough geometry to preserve."""
    return sum(len(block.text) for block in blocks) >= 40


def extract_ocr_text_blocks(
    pdf_path: str, source_language: str, max_pages: int | None = None
) -> List[TextBlock]:
    """Extract OCR lines with page coordinates for scanned PDFs.

    The previous fallback produced a new blank A4 document. These blocks let
    us keep the uploaded scan as the canvas and place translated paragraphs in
    their original visual areas.
    """
    document = fitz.open(pdf_path)
    blocks: List[TextBlock] = []
    try:
        language = TESSERACT_LANG_MAP.get(source_language.lower(), "eng")
        page_count = min(document.page_count, max_pages) if max_pages is not None else document.page_count
        for page_number in range(page_count):
            page = document[page_number]
            image = convert_from_path(
                pdf_path, first_page=page_number + 1, last_page=page_number + 1, dpi=300
            )[0]
            data = pytesseract.image_to_data(
                prepare_image_for_ocr(image), lang=language, config="--oem 1 --psm 6",
                output_type=pytesseract.Output.DICT,
            )
            # Keep each OCR line separate. On scans Tesseract can classify an
            # entire page as one paragraph; covering that broad box destroys
            # the page design. Line-level geometry retains headings, rules,
            # stamps, artwork, and document spacing.
            groups: dict[tuple[int, int, int], list[tuple[str, int, int, int, int, float]]] = {}
            for index, word in enumerate(data["text"]):
                word = word.strip()
                confidence = float(data["conf"][index])
                # Low-confidence OCR is usually scanner noise or a broken
                # glyph. Never send it to the translator as if it were text.
                if not word or confidence < 50:
                    continue
                key = (
                    int(data["block_num"][index]), int(data["par_num"][index]),
                    int(data["line_num"][index]),
                )
                groups.setdefault(key, []).append((
                    word, int(data["left"][index]), int(data["top"][index]),
                    int(data["width"][index]), int(data["height"][index]), confidence,
                ))

            scale_x = page.rect.width / image.width
            scale_y = page.rect.height / image.height
            for words in groups.values():
                text = " ".join(word[0] for word in words)
                left = min(word[1] for word in words)
                top = min(word[2] for word in words)
                right = max(word[1] + word[3] for word in words)
                bottom = max(word[2] + word[4] for word in words)
                average_height = sum(word[4] for word in words) / len(words)
                blocks.append(TextBlock(
                    page_number=page_number,
                    rect=(left * scale_x, top * scale_y, right * scale_x, bottom * scale_y),
                    text=text,
                    font_size=max(7.0, average_height * scale_y * 0.9),
                    color=(0, 0, 0),
                    is_bold=False,
                ))
    finally:
        document.close()
    return blocks


def _scan_background_color(page: fitz.Page, rect: fitz.Rect) -> tuple[float, float, float]:
    """Estimate the local scan background, avoiding conspicuous white boxes."""
    try:
        sample = page.get_pixmap(clip=rect, matrix=fitz.Matrix(0.15, 0.15), alpha=False)
        if sample.width <= 0 or sample.height <= 0:
            return (1, 1, 1)
        pixels = sample.samples
        channels = sample.n
        values = [pixels[index:index + channels] for index in range(0, len(pixels), channels)]
        # A median is robust against the dark ink inside the rectangle.
        color = tuple(sorted(pixel[channel] for pixel in values)[len(values) // 2] / 255 for channel in range(3))
        # Most scanned government pages are white. Removing near-white JPEG
        # tint prevents grey replacement bars while preserving genuine colour
        # artwork on covers and certificates.
        return tuple(1.0 if component > 0.82 else component for component in color)
    except Exception:
        return (1, 1, 1)


def _font_path(target_language: str, is_bold: bool) -> str | None:
    font_name = get_language_config(target_language)["font"]
    bundled_fonts = {
        "NotoSans": "NotoSans-Bold.ttf" if is_bold else "NotoSans-Regular.ttf",
        "NotoSansDevanagari": "NotoSansDevanagariWithLatin-Bold.ttf" if is_bold else "NotoSansDevanagariWithLatin-Regular.ttf",
        # The Gujarati-only Noto files omit Latin glyphs. Sarvam correctly
        # preserves useful terms such as "CA" and "PDF", so use the bundled
        # Gujarati + Latin composite rather than rendering those terms as □.
        "NotoSansGujarati": "NotoSansGujaratiWithLatin-Bold.ttf" if is_bold else "NotoSansGujaratiWithLatin-Regular.ttf",
    }
    filename = bundled_fonts.get(font_name)
    return os.path.join(FONTS_DIR, filename) if filename else None


def _fit_font_size(rect: fitz.Rect, original_size: float, text: str) -> float:
    """Start at the original visual type size; never silently create tiny text."""
    if rect.height < original_size * 1.35:
        return max(7.0, min(original_size, rect.height * 0.90))
    return max(8.0, original_size * 0.98)


def _expanded_text_rect(page: fitz.Page, rect: fitz.Rect, original_size: float) -> fitz.Rect:
    """Give an expanded Indic translation room before shrinking its type.

    Digital legal letters often encode each English line as an extremely short
    PDF span. Hindi, Marathi, and Gujarati need more vertical space. Expand
    only into immediately blank space, leaving headers, neighbouring columns,
    and page artwork intact.
    """
    padding = max(3.0, original_size * 0.55)
    top = max(0.0, rect.y0 - padding)
    bottom = min(page.rect.height, rect.y1 + max(padding, original_size * 1.5))
    return fitz.Rect(rect.x0, top, rect.x1, bottom)


def _preserved_prefix(text: str) -> tuple[str, str]:
    """Split an answer-choice marker from its translated content."""
    match = re.match(r"^(\([A-D]\)\s*)", text)
    return (match.group(1), text[match.end():]) if match else ("", text)


def _normalise_vision_table(text: str) -> str:
    """Turn Vision's HTML table output into readable rows for PDF drawing."""
    if "<table" not in text.lower():
        return text
    value = re.sub(r"(?i)</tr\s*>", "\n", text)
    value = re.sub(r"(?i)</t[dh]\s*>", "    ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"<[^>]+>", "", value)
    rows = [" ".join(unescape(row).split()) for row in value.splitlines()]
    return "\n".join(row for row in rows if row)


def _vision_table_rows(text: str) -> list[list[str]]:
    """Extract cells from a Sarvam Vision HTML table without extra packages."""
    rows: list[list[str]] = []
    for row in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", text):
        cells = []
        for cell in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row):
            value = re.sub(r"<[^>]+>", "", cell)
            value = " ".join(unescape(value).split())
            if value:
                cells.append(value)
        if cells:
            rows.append(cells)
    return rows


def _draw_vision_table(
    page: fitz.Page,
    rect: fitz.Rect,
    table_html: str,
    font_name: str,
    font_path: str | None,
    target_language: str,
) -> bool:
    """Rebuild Vision's table block as a legible two-column PDF table."""
    rows = _vision_table_rows(table_html)
    if len(rows) < 2:
        return False
    rect += (0.5, 0.5, -0.5, -0.5)
    header, data_rows = rows[0], rows[1:]
    left_edge = rect.x0
    split = rect.x0 + rect.width * 0.84
    header_height = min(22, max(15, rect.height * 0.045))
    page.draw_rect(fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + header_height), color=None, fill=(0.20, 0.43, 0.07), overlay=True)
    text_kwargs = {
        "fontname": font_name if font_path else "helv",
        "fontfile": font_path,
        "color": (1, 1, 1),
        "lineheight": 1.0,
        "overlay": True,
    }
    page.insert_textbox(fitz.Rect(left_edge + 4, rect.y0 + 1, split - 3, rect.y0 + header_height - 1), header[0], fontsize=10, **text_kwargs)
    if len(header) > 1:
        page.insert_textbox(fitz.Rect(split + 3, rect.y0 + 1, rect.x1 - 4, rect.y0 + header_height - 1), header[-1], fontsize=10, align=2, **text_kwargs)

    # Allocate taller rows to longer translated entries, while retaining the
    # original table's hierarchy and page-number column.
    weights = [max(1.0, (len(row[0]) if row else 0) / 43) for row in data_rows]
    available = rect.height - header_height
    unit = available / sum(weights)
    font_size = max(7.0, min(10.5, unit * 0.48))
    y = rect.y0 + header_height
    for row, weight in zip(data_rows, weights):
        row_height = unit * weight
        row_rect = fitz.Rect(rect.x0, y, rect.x1, y + row_height)
        left_rect = fitz.Rect(rect.x0 + 4, y + 1, split - 4, y + row_height - 1)
        right_rect = fitz.Rect(split + 4, y + 1, rect.x1 - 4, y + row_height - 1)
        page.insert_textbox(left_rect, row[0], fontname=font_name if font_path else "helv", fontfile=font_path, fontsize=font_size, color=(0.08, 0.08, 0.08), lineheight=1.02, overlay=True)
        if len(row) > 1:
            number = row[-1]
            badge = fitz.Rect(max(split + 4, rect.x1 - 35), y + 3, rect.x1 - 5, min(y + row_height - 3, y + 21))
            page.draw_rect(badge, color=None, fill=(0.88, 0.88, 0.88), overlay=True)
            page.insert_textbox(right_rect, number, fontname=font_name if font_path else "helv", fontfile=font_path, fontsize=font_size, color=(0.08, 0.08, 0.08), align=2, overlay=True)
        page.draw_line((rect.x0, y + row_height), (rect.x1, y + row_height), color=(0.0, 0.65, 0.95), width=0.7, overlay=True)
        y += row_height
    return True


def _is_static_label(text: str) -> bool:
    """Avoid translating answer-key labels and numeric response grids."""
    compact = text.strip()
    return bool(
        re.fullmatch(r"[\d\s.()\[\],:;A-D]+", compact)
        or compact.upper() in {"ANSWER KEY", "ANSWERS"}
    )


def create_layout_preserved_pdf(
    source_pdf_path: str,
    blocks: List[TextBlock],
    translated_blocks: List[str],
    output_path: str,
    target_language: str,
    page_limit: int | None = None,
    scan_overlay: bool = False,
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

        # Digital PDFs can redact only selectable text. A scanned page has no
        # text layer, so lightly cover OCR text lanes before placing the
        # translation; the original page artwork remains the canvas.
        for block, translation in zip(blocks, translated_blocks):
            if _is_static_label(block.text):
                continue
            if not translation or translation.strip() == block.text.strip():
                continue
            rect = fitz.Rect(block.rect)
            if scan_overlay:
                document[block.page_number].draw_rect(
                    rect, color=None,
                    fill=_scan_background_color(document[block.page_number], rect), overlay=True,
                )
            else:
                document[block.page_number].add_redact_annot(rect, fill=False, cross_out=False)

        if not scan_overlay:
            for page in document:
                page.apply_redactions(images=0, graphics=0, text=0)

        for block, translation in zip(blocks, translated_blocks):
            prefix, source_content = _preserved_prefix(block.text)
            if _is_static_label(block.text):
                continue
            is_vision_table = "<table" in translation.lower()
            page = document[block.page_number]
            font_path = _font_path(target_language, block.is_bold)
            font_name = "LipiTranslateBold" if block.is_bold else "LipiTranslateRegular"
            rect = fitz.Rect(block.rect)
            # Keep text inside its original visual lane and avoid table lines.
            rect += (0.5, 0.25, -0.5, -0.25)
            if is_vision_table and _draw_vision_table(
                page, rect, translation, font_name, font_path, target_language
            ):
                replaced += 1
                continue
            translation = _normalise_vision_table(translation)
            if "\n" not in translation:
                translation = " ".join(translation.split())
            if prefix:
                _, translation = _preserved_prefix(translation)
                # Preserve the source choice marker exactly once. Sarvam
                # usually returns it too, but the redaction removes the
                # original PDF text, so it must be part of the replacement.
                translation = f"{prefix}{translation}"
            if not translation or translation == source_content.strip():
                continue
            size = _fit_font_size(rect, block.font_size, translation)
            result = -1
            # Tables and long translated cells need a measured shrink loop;
            # two fixed attempts produced clipped/blank output.
            while size >= 7.0 and result < 0:
                result = page.insert_textbox(
                    rect, translation,
                    fontname=font_name if font_path else ("hebo" if block.is_bold else "helv"),
                    fontfile=font_path, fontsize=size, color=block.color,
                    lineheight=1.05, overlay=True,
                )
                if result < 0:
                    size = max(6.75, size * 0.82)
            # For digital source PDFs, do a second measured attempt with a
            # modest vertical expansion before declaring the text missing.
            # This avoids the old behaviour where translated legal headings
            # simply disappeared when an Indic sentence was longer.
            if result < 0 and not scan_overlay:
                expanded_rect = _expanded_text_rect(page, rect, block.font_size)
                size = max(7.0, min(block.font_size * 0.88, 10.5))
                while size >= 6.75 and result < 0:
                    result = page.insert_textbox(
                        expanded_rect, translation,
                        fontname=font_name if font_path else ("hebo" if block.is_bold else "helv"),
                        fontfile=font_path, fontsize=size, color=block.color,
                        lineheight=1.0, overlay=True,
                    )
                    if result < 0:
                        size *= 0.82
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
