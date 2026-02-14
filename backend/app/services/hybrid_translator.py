"""
Hybrid Translation Service - IMPROVED VERSION
==============================================
Orchestrates Sarvam AI (primary) and OpenAI (fallback) with intelligent
routing, blank page handling, and comprehensive statistics
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Confidence threshold for Sarvam -> OpenAI fallback
FALLBACK_CONFIDENCE_THRESHOLD = 80.0

# Maximum concurrent translation tasks
DEFAULT_CONCURRENCY = 4

# Minimum characters to attempt translation
MIN_CHARS_FOR_TRANSLATION = 10


# ============================================================================
# STATISTICS TRACKING
# ============================================================================

@dataclass
class TranslationStats:
    """Track translation statistics"""
    total_chunks: int = 0
    blank_pages: int = 0
    sarvam_success: int = 0
    sarvam_failed: int = 0
    openai_success: int = 0
    openai_failed: int = 0
    fallbacks: int = 0
    total_cost_inr: float = 0.0
    total_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    @property
    def sarvam_percentage(self) -> float:
        """Percentage of chunks translated by Sarvam"""
        total = self.sarvam_success + self.openai_success
        return (self.sarvam_success / total * 100) if total > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Overall success rate"""
        total = self.total_chunks - self.blank_pages
        success = self.sarvam_success + self.openai_success
        return (success / total * 100) if total > 0 else 0.0
    
    def log_summary(self):
        """Log statistics summary"""
        logger.info("=" * 70)
        logger.info("📊 Translation Statistics:")
        logger.info(f"   Total chunks: {self.total_chunks}")
        logger.info(f"   Blank pages: {self.blank_pages}")
        logger.info(f"   🌟 Sarvam AI: {self.sarvam_success} ({self.sarvam_percentage:.0f}%)")
        logger.info(f"   🎯 OpenAI: {self.openai_success} ({100-self.sarvam_percentage:.0f}%)")
        logger.info(f"   🔄 Fallbacks: {self.fallbacks}")
        logger.info(f"   ❌ Failures: {self.sarvam_failed + self.openai_failed}")
        logger.info(f"   💰 Total cost: ₹{self.total_cost_inr:.2f}")
        logger.info(f"   ⏱️  Total time: {self.total_time:.1f}s")
        logger.info(f"   ✅ Success rate: {self.success_rate:.1f}%")
        if self.errors:
            logger.warning(f"   Errors encountered: {len(self.errors)}")
        logger.info("=" * 70)


# ============================================================================
# HYBRID TRANSLATOR
# ============================================================================

class HybridTranslatorV2:
    """
    Hybrid translator combining Sarvam AI and OpenAI
    """
    
    def __init__(
        self,
        source_language: str,
        target_language: str,
        mode: str = "general",
        concurrency: int = DEFAULT_CONCURRENCY,
        sarvam_translator = None,
        openai_translator = None
    ):
        """
        Initialize hybrid translator
        
        Args:
            source_language: Source language code
            target_language: Target language code
            mode: Translation mode (general, formal, casual, technical)
            concurrency: Maximum concurrent translations
            sarvam_translator: Optional Sarvam translator instance
            openai_translator: Optional OpenAI translator instance
        """
        self.source_language = source_language
        self.target_language = target_language
        self.mode = mode
        self.concurrency = concurrency
        
        # Initialize translators (lazy import to avoid circular deps)
        if sarvam_translator is None:
            from app.sarvam_wrapper import SarvamTranslator
            self.sarvam = SarvamTranslator()
        else:
            self.sarvam = sarvam_translator
        
        if openai_translator is None:
            from app.openai_wrapper import OpenAITranslator
            self.openai = OpenAITranslator()
        else:
            self.openai = openai_translator
        
        # Statistics
        self.stats = TranslationStats()
        
        logger.info("🌟 Hybrid Translator V2 initialized")
        logger.info(f"   {source_language} → {target_language}")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Primary: Sarvam AI")
        logger.info(f"   Fallback: OpenAI GPT-4o")
        logger.info(f"   Concurrency: {concurrency}")
    
    
    def _is_blank_or_minimal(self, text: str) -> bool:
        """Check if text is blank or too short to translate"""
        if not text:
            return True
        cleaned = text.strip()
        return len(cleaned) < MIN_CHARS_FOR_TRANSLATION
    
    
    async def translate_chunk(self, text: str, chunk_index: int) -> str:
        """
        Translate a single chunk with fallback logic
        
        Args:
            text: Text chunk to translate
            chunk_index: Index for logging
            
        Returns:
            Translated text
        """
        # Skip blank/minimal text
        if self._is_blank_or_minimal(text):
            logger.info(f"   Chunk {chunk_index + 1}: BLANK (skipped)")
            self.stats.blank_pages += 1
            return ""
        
        logger.info(f"   Chunk {chunk_index + 1}: Translating ({len(text)} chars)")
        
        # Try Sarvam AI first
        try:
            result = await self.sarvam.translate(
                text,
                self.source_language,
                self.target_language
            )
            
            if result["success"]:
                confidence = result.get("confidence", 95.0)
                
                # Check if confidence is acceptable
                if confidence >= FALLBACK_CONFIDENCE_THRESHOLD:
                    self.stats.sarvam_success += 1
                    self.stats.total_cost_inr += result.get("cost_inr", 0.0)
                    logger.info(f"   ✅ Sarvam success (confidence: {confidence:.1f}%)")
                    return result["translated_text"]
                else:
                    # Low confidence, fallback to OpenAI
                    logger.info(f"   🔄 Falling back to OpenAI (confidence: {confidence:.1f}%)")
                    self.stats.fallbacks += 1
                    
            else:
                # Sarvam failed, fallback to OpenAI
                error = result.get("error", "Unknown error")
                logger.warning(f"   ⚠️ Sarvam failed: {error}")
                logger.info(f"   🔄 Falling back to OpenAI")
                self.stats.sarvam_failed += 1
                self.stats.fallbacks += 1
                self.stats.errors.append(f"Sarvam chunk {chunk_index + 1}: {error}")
                
        except Exception as e:
            logger.error(f"   ❌ Sarvam exception: {e}")
            logger.info(f"   🔄 Falling back to OpenAI")
            self.stats.sarvam_failed += 1
            self.stats.fallbacks += 1
            self.stats.errors.append(f"Sarvam chunk {chunk_index + 1}: {str(e)}")
        
        # Fallback to OpenAI
        try:
            result = await self.openai.translate(
                text,
                self.source_language,
                self.target_language,
                self.mode
            )
            
            if result["success"]:
                self.stats.openai_success += 1
                self.stats.total_cost_inr += result.get("cost_inr", 0.0)
                logger.info(f"   ✅ OpenAI success")
                return result["translated_text"]
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"   ❌ OpenAI also failed: {error}")
                self.stats.openai_failed += 1
                self.stats.errors.append(f"OpenAI chunk {chunk_index + 1}: {error}")
                
                # Return original text as last resort
                return text
                
        except Exception as e:
            logger.error(f"   ❌ OpenAI exception: {e}")
            self.stats.openai_failed += 1
            self.stats.errors.append(f"OpenAI chunk {chunk_index + 1}: {str(e)}")
            
            # Return original text as last resort
            return text
    
    
    async def translate_chunks(self, chunks: List[str]) -> List[str]:
        """
        Translate multiple chunks with concurrency control
        
        Args:
            chunks: List of text chunks to translate
            
        Returns:
            List of translated chunks
        """
        self.stats.total_chunks = len(chunks)
        self.stats.total_time = time.time()
        
        logger.info(f"🌍 Translating {len(chunks)} chunks...")
        logger.info(f"   Concurrency: {self.concurrency}")
        
        # Create translation tasks with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def translate_with_semaphore(text: str, index: int) -> str:
            async with semaphore:
                return await self.translate_chunk(text, index)
        
        # Execute all translations concurrently (up to concurrency limit)
        tasks = [
            translate_with_semaphore(chunk, i)
            for i, chunk in enumerate(chunks)
        ]
        
        translated_chunks = await asyncio.gather(*tasks)
        
        # Update statistics
        self.stats.total_time = time.time() - self.stats.total_time
        
        logger.info("✅ Translation complete")
        self.stats.log_summary()
        
        return translated_chunks
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get translation statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_chunks": self.stats.total_chunks,
            "blank_pages": self.stats.blank_pages,
            "sarvam_used": self.stats.sarvam_success,
            "openai_used": self.stats.openai_success,
            "fallbacks": self.stats.fallbacks,
            "total_cost_inr": self.stats.total_cost_inr,
            "total_time": self.stats.total_time,
            "sarvam_percentage": self.stats.sarvam_percentage,
            "success_rate": self.stats.success_rate,
            "errors": self.stats.errors
        }
    
    
    async def close(self):
        """Close translator connections"""
        if hasattr(self.sarvam, 'close'):
            await self.sarvam.close()


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def translate_document(
    pages: List[str],
    source_language: str,
    target_language: str,
    mode: str = "general",
    concurrency: int = DEFAULT_CONCURRENCY
) -> tuple[List[str], Dict[str, Any]]:
    """
    Translate a document (list of pages)
    
    Args:
        pages: List of page texts
        source_language: Source language
        target_language: Target language
        mode: Translation mode
        concurrency: Concurrent translations
        
    Returns:
        Tuple of (translated_pages, statistics)
    """
    translator = HybridTranslatorV2(
        source_language=source_language,
        target_language=target_language,
        mode=mode,
        concurrency=concurrency
    )
    
    try:
        translated = await translator.translate_chunks(pages)
        stats = translator.get_statistics()
        return translated, stats
    finally:
        await translator.close()