# app/services/translator.py
# ============================================================================
# REWRITTEN — mode is stored and passed; logging shows content detection.
# ============================================================================

from typing import List
import asyncio
import logging
from app.openai_wrapper import get_openai_client, TRANSLATION_MODEL

logger = logging.getLogger(__name__)


class TranslatorService:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        mode: str = "general",
        model: str | None = None,
        concurrency: int = 8,
    ):
        self.source_language = source_language
        self.target_language = target_language
        self.mode            = mode                          # ✅ stored
        self.model           = model or TRANSLATION_MODEL
        self.concurrency     = concurrency
        self.semaphore       = asyncio.Semaphore(self.concurrency)

        logger.info("🚀 Translator initialised")
        logger.info(f"   {source_language} → {target_language}")
        logger.info(f"   Mode: {mode} | Concurrency: {concurrency}")

    async def _translate_one(self, idx: int, chunk: str):
        async with self.semaphore:
            logger.info(f"🌐 Chunk {idx} started ({len(chunk)} chars)")
            client = get_openai_client()

            result = await client.translate_text_async(
                text=chunk,
                source_language=self.source_language,
                target_language=self.target_language,
                model=self.model,
                mode=self.mode,                              # ✅ passed through
            )

            logger.info(f"✅ Chunk {idx} done ({len(result['text'])} chars)")
            return idx, result["text"]

    async def translate_chunks(self, chunks: List[str]) -> List[str]:
        tasks = [self._translate_one(i + 1, chunk) for i, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)
        results.sort(key=lambda x: x[0])          # preserve order
        return [text for _, text in results]