"""Sarvam-only translation service.

The public class name is retained for backwards compatibility with existing
callers, but this module deliberately has no fallback provider. Gemini is used
separately by the PDF visualization service only.
"""

import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.sarvam_wrapper import SarvamTranslator, sanitize_text_for_sarvam

logger = logging.getLogger(__name__)
# Sarvam can rate-limit parallel requests, especially for scanned PDFs which
# contain many small OCR blocks. Keep a small bounded pool: two requests make
# multi-block pages materially faster while avoiding the burst of 429s caused
# by unbounded fan-out. Operators can lower this to 1 or raise it cautiously
# with SARVAM_TRANSLATION_CONCURRENCY.
DEFAULT_CONCURRENCY = max(1, int(os.getenv("SARVAM_TRANSLATION_CONCURRENCY", "2")))
# Short OCR lines can be meaningful document content (names, headings, dates,
# and labels). Skipping everything below ten characters caused Marathi/Hindi
# fragments to remain in the source language. Keep only truly minimal OCR
# noise out of Sarvam requests.
MIN_CHARS_FOR_TRANSLATION = 2
# Sarvam Translate accepts at most 2,000 characters. Leave room for any
# preprocessing by keeping each request under this threshold.
MAX_SARVAM_INPUT_CHARS = 1900
# OCR layout extraction commonly produces dozens of short spans per page. A
# stable separator lets us translate several spans in one Sarvam request while
# still mapping each response back to its original rectangle.
BATCH_SEPARATOR = "\n⟦LIPI_BLOCK_BREAK⟧\n"


@dataclass
class TranslationStats:
    """Metrics for Sarvam translation requests in one document."""

    total_chunks: int = 0
    blank_pages: int = 0
    sarvam_success: int = 0
    sarvam_failed: int = 0
    total_cost_inr: float = 0.0
    total_time: float = 0.0
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        attempted = self.total_chunks - self.blank_pages
        return (self.sarvam_success / attempted * 100) if attempted else 0.0


class HybridTranslatorV2:
    """Translate chunks exclusively with Sarvam AI.

    ``HybridTranslatorV2`` is retained as an import-compatible name. No OpenAI
    client is constructed or called by this service.
    """

    def __init__(
        self,
        source_language: str,
        target_language: str,
        mode: str = "general",
        concurrency: int = DEFAULT_CONCURRENCY,
        sarvam_translator: SarvamTranslator | None = None,
    ):
        self.source_language = source_language
        self.target_language = target_language
        self.mode = mode
        self.concurrency = max(1, concurrency)
        self.sarvam = sarvam_translator or SarvamTranslator()
        self.stats = TranslationStats()
        logger.info("Sarvam-only translator initialized: %s -> %s", source_language, target_language)

    @staticmethod
    def _is_blank_or_minimal(text: str) -> bool:
        return not text or len(text.strip()) < MIN_CHARS_FOR_TRANSLATION

    @staticmethod
    def _split_for_sarvam(text: str) -> List[str]:
        """Split long page text at sentence boundaries without dropping text."""
        if len(text) <= MAX_SARVAM_INPUT_CHARS:
            return [text]

        units = re.split(r"(?<=[.!?।])\s+|\n+", text)
        pieces: List[str] = []
        current = ""
        for unit in units:
            unit = unit.strip()
            if not unit:
                continue
            if current and len(current) + len(unit) + 1 > MAX_SARVAM_INPUT_CHARS:
                pieces.append(current)
                current = ""
            # A single long sentence is safely divided as a last resort.
            while len(unit) > MAX_SARVAM_INPUT_CHARS:
                if current:
                    pieces.append(current)
                    current = ""
                pieces.append(unit[:MAX_SARVAM_INPUT_CHARS])
                unit = unit[MAX_SARVAM_INPUT_CHARS:]
            current = f"{current} {unit}".strip()
        if current:
            pieces.append(current)
        return pieces or [text]

    async def translate_chunk(self, text: str, chunk_index: int) -> str:
        if self._is_blank_or_minimal(text):
            self.stats.blank_pages += 1
            return ""

        translated_parts: List[str] = []
        for part_index, part in enumerate(self._split_for_sarvam(text), start=1):
            part = sanitize_text_for_sarvam(part)
            if not part.strip():
                continue
            try:
                result = await self.sarvam.translate(part, self.source_language, self.target_language)
            except Exception as exc:
                self.stats.sarvam_failed += 1
                self.stats.errors.append(f"Sarvam chunk {chunk_index + 1}.{part_index}: {exc}")
                logger.exception("Sarvam request failed for chunk %s.%s", chunk_index + 1, part_index)
                return text

            if not (result.get("success") and result.get("translated_text", "").strip()):
                error = result.get("error", "Sarvam returned no translated text")
                self.stats.sarvam_failed += 1
                self.stats.errors.append(f"Sarvam chunk {chunk_index + 1}.{part_index}: {error}")
                logger.error("Sarvam failed for chunk %s.%s: %s", chunk_index + 1, part_index, error)
                # Keep the source page rather than silently sending it to another model.
                return text
            translated_parts.append(result["translated_text"])
            self.stats.total_cost_inr += float(result.get("cost_inr", 0.0))

        if not translated_parts:
            self.stats.blank_pages += 1
            return ""

        self.stats.sarvam_success += 1
        return "\n\n".join(translated_parts)

    async def translate_chunks(self, chunks: List[str]) -> List[str]:
        self.stats.total_chunks = len(chunks)
        started_at = time.monotonic()
        semaphore = asyncio.Semaphore(self.concurrency)

        async def translate_with_limit(text: str, index: int) -> str:
            async with semaphore:
                return await self.translate_chunk(text, index)

        translated = await asyncio.gather(
            *(translate_with_limit(chunk, index) for index, chunk in enumerate(chunks))
        )
        self.stats.total_time = time.monotonic() - started_at
        return translated

    def _batch_block_indices(self, blocks: List[str]) -> List[List[int]]:
        batches: List[List[int]] = []
        current: List[int] = []
        current_length = 0
        for index, block in enumerate(blocks):
            text = sanitize_text_for_sarvam(block or "").strip()
            if self._is_blank_or_minimal(text):
                continue
            added = len(text) + (len(BATCH_SEPARATOR) if current else 0)
            if current and current_length + added > MAX_SARVAM_INPUT_CHARS:
                batches.append(current)
                current = []
                current_length = 0
                added = len(text)
            current.append(index)
            current_length += added
        if current:
            batches.append(current)
        return batches

    async def _translate_block_batch(self, blocks: List[str], indices: List[int]) -> Dict[int, str]:
        source = BATCH_SEPARATOR.join(
            sanitize_text_for_sarvam(blocks[index]).strip() for index in indices
        )
        result = await self.sarvam.translate(source, self.source_language, self.target_language)
        if not (result.get("success") and result.get("translated_text", "").strip()):
            raise ValueError(result.get("error", "Sarvam returned no translated text"))
        translated_parts = result["translated_text"].split(BATCH_SEPARATOR)
        if len(translated_parts) != len(indices):
            # Sarvam occasionally normalizes the separator. Do not silently
            # misalign text with PDF rectangles; fall back to safe per-block
            # calls for this batch instead.
            raise ValueError("batch separator was not preserved")
        self.stats.total_cost_inr += float(result.get("cost_inr", 0.0))
        return {index: part.strip() for index, part in zip(indices, translated_parts)}

    async def translate_layout_blocks(self, blocks: List[str]) -> List[str]:
        """Translate OCR/native layout spans in bounded batches.

        This avoids one network round trip per tiny OCR span (the main cause of
        multi-minute 35% stalls) while retaining a strict index mapping. Any
        batch whose separator is altered is retried safely span-by-span.
        """
        self.stats.total_chunks = len(blocks)
        started_at = time.monotonic()
        translated = list(blocks)
        batches = self._batch_block_indices(blocks)
        semaphore = asyncio.Semaphore(self.concurrency)

        async def run_batch(indices: List[int]) -> None:
            async with semaphore:
                try:
                    mapped = await self._translate_block_batch(blocks, indices)
                    for index, value in mapped.items():
                        translated[index] = value
                    self.stats.sarvam_success += len(indices)
                except Exception as batch_error:
                    logger.warning("Batch translation fallback for %s spans: %s", len(indices), batch_error)
                    for index in indices:
                        translated[index] = await self.translate_chunk(blocks[index], index)

        await asyncio.gather(*(run_batch(indices) for indices in batches))
        self.stats.total_time = time.monotonic() - started_at
        return translated

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_chunks": self.stats.total_chunks,
            "blank_pages": self.stats.blank_pages,
            "sarvam_used": self.stats.sarvam_success,
            "sarvam_failed": self.stats.sarvam_failed,
            "total_cost_inr": self.stats.total_cost_inr,
            "total_time": self.stats.total_time,
            "success_rate": self.stats.success_rate,
            "errors": self.stats.errors,
        }

    async def close(self) -> None:
        await self.sarvam.close()


async def translate_document(
    pages: List[str], source_language: str, target_language: str,
    mode: str = "general", concurrency: int = DEFAULT_CONCURRENCY,
) -> tuple[List[str], Dict[str, Any]]:
    translator = HybridTranslatorV2(source_language, target_language, mode, concurrency)
    try:
        translated = await translator.translate_chunks(pages)
        return translated, translator.get_statistics()
    finally:
        await translator.close()
