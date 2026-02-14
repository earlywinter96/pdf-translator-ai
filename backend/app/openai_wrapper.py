"""
OpenAI Translation Wrapper - IMPROVED VERSION
==============================================
Enhanced GPT-4o translation with better prompts, validation, and error handling
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_TIMEOUT = 45.0  # Increased from 30s

# Cost per 1M tokens (in USD)
INPUT_COST_PER_1M = 2.50
OUTPUT_COST_PER_1M = 10.00

# USD to INR conversion rate (approximate)
USD_TO_INR = 83.0

# Token estimation (rough: 1 token ≈ 4 chars)
CHARS_PER_TOKEN = 4

# Max retries
MAX_RETRIES = 2
RETRY_DELAY = 3.0


# ============================================================================
# LANGUAGE NAMES
# ============================================================================

LANGUAGE_NAMES = {
    "gujarati": "Gujarati",
    "hindi": "Hindi",
    "marathi": "Marathi",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "kannada": "Kannada",
    "malayalam": "Malayalam",
    "bengali": "Bengali",
    "punjabi": "Punjabi",
    "english": "English",
    "gu": "Gujarati",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "pa": "Punjabi",
    "en": "English"
}


# ============================================================================
# OPENAI CLIENT
# ============================================================================

class OpenAITranslator:
    """OpenAI GPT-4o Translation Client"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            timeout=OPENAI_TIMEOUT
        )
        
        logger.info(f"✅ OpenAI wrapper ready")
        logger.info(f"   Model: {OPENAI_MODEL}")
        logger.info(f"   Timeout: {OPENAI_TIMEOUT}s")
        logger.info(f"   Max retries: {MAX_RETRIES}")
    
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get display name for language"""
        return LANGUAGE_NAMES.get(lang_code.lower(), lang_code.title())
    
    
    def _build_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        mode: str = "general"
    ) -> str:
        """
        Build translation system prompt
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language  
            mode: Translation mode (general, formal, casual, technical)
            
        Returns:
            Formatted prompt
        """
        source_name = self._get_language_name(source_language)
        target_name = self._get_language_name(target_language)
        
        # Mode-specific instructions
        mode_instructions = {
            "general": "natural and fluent",
            "formal": "formal and professional",
            "casual": "casual and conversational",
            "technical": "precise and technical"
        }
        
        style = mode_instructions.get(mode, "natural and fluent")
        
        return f"""You are an expert translator specializing in {source_name} to {target_name} translation.

CRITICAL INSTRUCTIONS:
1. **Language Validation**: First, check if the input text is actually in {source_name}. If it's already in {target_name} or a different language, handle appropriately.

2. **Translation Quality**: Provide a {style} translation that:
   - Preserves the original meaning and nuances
   - Uses natural {target_name} phrasing
   - Maintains the tone and style of the source
   - Handles cultural context appropriately

3. **Format Preservation**: 
   - Keep line breaks, paragraphs, and spacing
   - Preserve numbers, dates, and proper nouns
   - Maintain any special formatting

4. **Output Format**: Return ONLY the translated text, nothing else. No explanations, no preambles, no meta-commentary.

INPUT TEXT TO TRANSLATE:
{text}

TRANSLATE TO {target_name.upper()}:"""
    
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        mode: str = "general"
    ) -> Dict[str, Any]:
        """
        Translate text using OpenAI GPT-4o
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            mode: Translation mode
            
        Returns:
            Translation result dictionary
        """
        # Validate input
        if not text or not text.strip():
            return {
                "translated_text": "",
                "confidence": 100.0,
                "cost_inr": 0.0,
                "success": True,
                "error": None,
                "note": "Empty input, skipped translation"
            }
        
        source_name = self._get_language_name(source_language)
        target_name = self._get_language_name(target_language)
        
        logger.info(f"🎯 Translating with OpenAI: {source_name} → {target_name}")
        logger.info(f"   Text length: {len(text)} chars")
        logger.info(f"   Mode: {mode}")
        
        start_time = time.time()
        
        # Attempt translation with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = await self._make_request(text, source_language, target_language, mode)
                
                if result["success"]:
                    elapsed = time.time() - start_time
                    logger.info(f"   ✅ OpenAI translation complete in {elapsed:.2f}s")
                    logger.info(f"   Cost: ₹{result['cost_inr']:.4f}")
                    
                    return {
                        **result,
                        "elapsed_time": elapsed
                    }
                else:
                    if attempt < MAX_RETRIES:
                        logger.warning(f"   ⚠️ Attempt {attempt} failed, retrying...")
                        await self._sleep(RETRY_DELAY)
                        continue
                    else:
                        return result
                        
            except Exception as e:
                logger.error(f"   ❌ Attempt {attempt} error: {e}")
                if attempt < MAX_RETRIES:
                    await self._sleep(RETRY_DELAY)
                else:
                    return {
                        "translated_text": text,
                        "confidence": 0.0,
                        "cost_inr": 0.0,
                        "success": False,
                        "error": str(e)
                    }
        
        return {
            "translated_text": text,
            "confidence": 0.0,
            "cost_inr": 0.0,
            "success": False,
            "error": "Max retries exceeded"
        }
    
    
    async def _make_request(
        self,
        text: str,
        source_language: str,
        target_language: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Make API request to OpenAI
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            mode: Translation mode
            
        Returns:
            Response dictionary
        """
        prompt = self._build_translation_prompt(text, source_language, target_language, mode)
        
        try:
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Follow instructions exactly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
                max_tokens=4000,
                timeout=OPENAI_TIMEOUT
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost_usd = (
                (input_tokens / 1_000_000 * INPUT_COST_PER_1M) +
                (output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)
            )
            cost_inr = cost_usd * USD_TO_INR
            
            return {
                "translated_text": translated_text,
                "confidence": 90.0,  # OpenAI generally high quality
                "cost_inr": cost_inr,
                "success": True,
                "error": None,
                "tokens_used": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return {
                "translated_text": text,
                "confidence": 0.0,
                "cost_inr": 0.0,
                "success": False,
                "error": str(e)
            }
    
    
    async def _sleep(self, seconds: float):
        """Async sleep"""
        import asyncio
        await asyncio.sleep(seconds)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def translate_with_openai(
    text: str,
    source_language: str,
    target_language: str,
    mode: str = "general"
) -> Dict[str, Any]:
    """
    Convenience function for one-off translations
    
    Args:
        text: Text to translate
        source_language: Source language
        target_language: Target language
        mode: Translation mode
        
    Returns:
        Translation result
    """
    translator = OpenAITranslator()
    result = await translator.translate(text, source_language, target_language, mode)
    return result