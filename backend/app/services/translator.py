# app/services/translator.py
# ============================================================================
# HARD-TIMEOUT SAFE ASYNC TRANSLATOR (NO HANGS)
# ============================================================================

from typing import List, Callable, Optional
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.openai_wrapper import get_openai_client

logger = logging.getLogger(__name__)


class UltraTranslatorService:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        mode: str = "general",
        model: Optional[str] = None,
        concurrency: int = 2,
        per_chunk_timeout: float = 40.0,  # 🔒 HARD LIMIT
    ):
        self.source_language = source_language
        self.target_language = target_language
        self.mode = mode
        self.model = model
        self.concurrency = concurrency
        self.per_chunk_timeout = per_chunk_timeout

        self.client = get_openai_client()

        # 🔒 Controlled executor (CRITICAL)
        self.executor = ThreadPoolExecutor(max_workers=concurrency)

        logger.info("🚀 Translator initialized")
        logger.info(f"   {source_language} → {target_language}")
        logger.info(f"   Concurrency: {concurrency}")
        logger.info(f"   Timeout/chunk: {per_chunk_timeout}s")

    # ------------------------------------------------------------------
    # SYNC TRANSLATION (BLOCKING)
    # ------------------------------------------------------------------
    def _translate_sync(self, chunk: str) -> str:
        if not chunk.strip():
            return ""

        logger.info(f"🧠 Translating chunk ({len(chunk)} chars)")

        try:
            result = self.client.translate_text(
                text=chunk,
                source_language=self.source_language,
                target_language=self.target_language,
                model=self.model,
                mode=self.mode,
            )

            text = result.get("text", "")
            return text if text.strip() else chunk

        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            return chunk

    # ------------------------------------------------------------------
    # ASYNC SAFE TRANSLATION
    # ------------------------------------------------------------------
    async def translate_chunks(
        self,
        chunks,
        progress_callback=None,
    ):
        if not chunks:
            return []

        loop = asyncio.get_running_loop()
        total = len(chunks)
        completed = 0
        results = [None] * total
        failed_indices = []

        logger.info(f"🚀 Translating {total} chunks")

        async def run_one(index, chunk):
            nonlocal completed
            try:
                translated = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._translate_sync,
                        chunk,
                    ),
                    timeout=self.per_chunk_timeout,
                )
                results[index] = translated
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Chunk {index+1} timed out (will retry serially)")
                failed_indices.append(index)
                results[index] = None

            completed += 1
            if progress_callback:
                progress_callback(completed, total)

        # -------------------------
        # PHASE 1: CONCURRENT
        # -------------------------
        await asyncio.gather(
            *[run_one(i, chunk) for i, chunk in enumerate(chunks)]
        )

        # -------------------------
        # PHASE 2: SERIAL RETRY
        # -------------------------
        if failed_indices:
            logger.info(f"🔁 Retrying {len(failed_indices)} chunks serially")

        for index in failed_indices:
            try:
                translated = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._translate_sync,
                        chunks[index],
                    ),
                    timeout=self.per_chunk_timeout,
                )
                results[index] = translated
                logger.info(f"✅ Chunk {index+1} translated on retry")
            except asyncio.TimeoutError:
                logger.error(
                    f"❌ Chunk {index+1} failed after retry — using original"
                )
                results[index] = chunks[index]

            if progress_callback:
                progress_callback(total, total)

        logger.info("✅ Translation complete")
        return results


ImprovedTranslatorService = UltraTranslatorService
