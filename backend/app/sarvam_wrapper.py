"""
Sarvam AI Translation Wrapper - IMPROVED VERSION
=================================================
Enhanced wrapper with better error handling, retry logic, and validation
"""

import os
import logging
import time
import unicodedata
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_API_URL = os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/translate")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-translate:v1")

# Sarvam Translate V1 list price: ₹20 per 10,000 characters.
# Keep this metric accurate even while startup credits make current calls free.
COST_PER_1K_CHARS = 2.00

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
BACKOFF_MULTIPLIER = 2.0

# Request timeout
REQUEST_TIMEOUT = 30.0

# Sarvam Translate supports all 22 scheduled Indian languages plus English.
SUPPORTED_LANGUAGES = {
    "bengali": "bn-IN",
    "gujarati": "gu-IN",
    "hindi": "hi-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "marathi": "mr-IN",
    "odia": "od-IN",
    "punjabi": "pa-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "english": "en-IN",
    "assamese": "as-IN",
    "bodo": "brx-IN",
    "dogri": "doi-IN",
    "konkani": "kok-IN",
    "kashmiri": "ks-IN",
    "maithili": "mai-IN",
    "manipuri": "mni-IN",
    "nepali": "ne-IN",
    "sanskrit": "sa-IN",
    "santali": "sat-IN",
    "sindhi": "sd-IN",
    "urdu": "ur-IN",
    # Short codes
    "bn": "bn-IN",
    "gu": "gu-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "od": "od-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "en": "en-IN",
    "as": "as-IN", "brx": "brx-IN", "doi": "doi-IN", "kok": "kok-IN",
    "ks": "ks-IN", "mai": "mai-IN", "mni": "mni-IN", "ne": "ne-IN",
    "sa": "sa-IN", "sat": "sat-IN", "sd": "sd-IN", "ur": "ur-IN",
}


def sanitize_text_for_sarvam(text: str) -> str:
    """Remove PDF control/format characters that Sarvam rejects.

    PDF extraction can include NUL, vertical-tab, form-feed, and invisible
    Unicode format characters. Keep normal spaces, tabs, and newlines so
    document structure is preserved.
    """
    normalized = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return "".join(
        char for char in normalized
        if char in {"\n", "\t"} or not unicodedata.category(char).startswith("C")
    )


# ============================================================================
# LANGUAGE VALIDATION
# ============================================================================

def validate_language(language: str) -> str:
    """
    Validate and normalize language code
    
    Args:
        language: Language name or code
        
    Returns:
        Normalized language code (e.g., 'hi-IN')
        
    Raises:
        ValueError: If language not supported
    """
    normalized = language.lower().strip()
    
    if normalized in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[normalized]
    
    # Check if already in the provider format, case-insensitively. The UI
    # normally sends names such as "hindi", while API clients may use hi-IN.
    for language_code in set(SUPPORTED_LANGUAGES.values()):
        if normalized == language_code.lower():
            return language_code
    
    raise ValueError(
        f"Language '{language}' not supported by Sarvam AI. "
        f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
    )


def is_same_language(source: str, target: str) -> bool:
    """
    Check if source and target are the same language
    
    Args:
        source: Source language code
        target: Target language code
        
    Returns:
        True if same language
    """
    try:
        src = validate_language(source)
        tgt = validate_language(target)
        return src == tgt
    except ValueError:
        return False


# ============================================================================
# SARVAM AI CLIENT
# ============================================================================

class SarvamTranslator:
    """Sarvam AI Translation Client"""
    
    def __init__(self):
        """Initialize Sarvam AI client"""
        if not SARVAM_API_KEY:
            raise ValueError("SARVAM_API_KEY not found in environment")
        
        self.api_key = SARVAM_API_KEY
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        
        logger.info("🌟 Sarvam AI Translator initialized")
        logger.info(f"   Model: {SARVAM_MODEL}")
        logger.info(f"   Supported languages: {len(SUPPORTED_LANGUAGES)}")
        logger.info(f"   Max retries: {MAX_RETRIES}")
    
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Translate text using Sarvam AI
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translation result dictionary with:
            - translated_text: Translated text
            - confidence: Translation confidence (0-100)
            - cost_inr: Cost in INR
            - success: Whether translation succeeded
            - error: Error message if failed
        """
        # PDF extraction can introduce invisible control characters rejected by
        # the translation endpoint. Sanitize before validation and billing.
        text = sanitize_text_for_sarvam(text)
        if not text or not text.strip():
            return {
                "translated_text": "",
                "confidence": 100.0,
                "cost_inr": 0.0,
                "success": True,
                "error": None,
                "note": "Empty input, skipped translation"
            }
        
        # Check if same language
        if is_same_language(source_language, target_language):
            logger.warning(f"⚠️ Source and target are the same language: {source_language}")
            return {
                "translated_text": text,
                "confidence": 100.0,
                "cost_inr": 0.0,
                "success": True,
                "error": None,
                "note": "Same language, no translation needed"
            }
        
        # Normalize language codes
        try:
            source_code = validate_language(source_language)
            target_code = validate_language(target_language)
        except ValueError as e:
            logger.error(f"❌ Language validation failed: {e}")
            return {
                "translated_text": text,
                "confidence": 0.0,
                "cost_inr": 0.0,
                "success": False,
                "error": str(e)
            }
        
        logger.info(f"🌍 Translating with Sarvam AI: {source_code} → {target_code}")
        logger.info(f"   Text length: {len(text)} chars")
        
        start_time = time.time()
        
        # Attempt translation with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._make_request(text, source_code, target_code)
                
                if response["success"]:
                    elapsed = time.time() - start_time
                    cost = self._calculate_cost(text)
                    
                    logger.info(f"   ✅ Sarvam translation complete in {elapsed:.2f}s")
                    logger.info(f"   Confidence: {response['confidence']:.2f}%")
                    logger.info(f"   Cost: ₹{cost:.4f}")
                    
                    return {
                        **response,
                        "cost_inr": cost,
                        "elapsed_time": elapsed
                    }
                else:
                    # Handle API errors
                    if attempt < MAX_RETRIES:
                        delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** (attempt - 1))
                        logger.warning(f"   ⚠️ Attempt {attempt} failed, retrying in {delay}s...")
                        await self._sleep(delay)
                        continue
                    else:
                        logger.error(f"   ❌ All {MAX_RETRIES} attempts failed")
                        return response
                        
            except Exception as e:
                logger.error(f"   ❌ Attempt {attempt} error: {e}")
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** (attempt - 1))
                    await self._sleep(delay)
                else:
                    return {
                        "translated_text": text,
                        "confidence": 0.0,
                        "cost_inr": 0.0,
                        "success": False,
                        "error": str(e)
                    }
        
        # Should never reach here
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
        source_code: str,
        target_code: str
    ) -> Dict[str, Any]:
        """
        Make API request to Sarvam
        
        Args:
            text: Text to translate
            source_code: Source language code
            target_code: Target language code
            
        Returns:
            Response dictionary
        """
        payload = {
            "input": text,
            "source_language_code": source_code,
            "target_language_code": target_code,
            "speaker_gender": "Male",
            "mode": "formal",
            "model": SARVAM_MODEL,
            "enable_preprocessing": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key
        }
        
        response = await self.client.post(
            SARVAM_API_URL,
            json=payload,
            headers=headers
        )
        
        # Handle response
        if response.status_code == 200:
            data = response.json()
            return {
                "translated_text": data.get("translated_text", ""),
                "confidence": 95.0,  # Sarvam doesn't provide confidence, assume high
                "success": True,
                "error": None
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            
            logger.error(f"❌ Sarvam API error: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            
            return {
                "translated_text": text,
                "confidence": 0.0,
                "success": False,
                "error": f"API error {response.status_code}: {error_msg}"
            }
    
    
    def _calculate_cost(self, text: str) -> float:
        """
        Calculate translation cost
        
        Args:
            text: Input text
            
        Returns:
            Cost in INR
        """
        char_count = len(text)
        return (char_count / 1000.0) * COST_PER_1K_CHARS
    
    
    async def _sleep(self, seconds: float):
        """Async sleep"""
        import asyncio
        await asyncio.sleep(seconds)
    
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def translate_with_sarvam(
    text: str,
    source_language: str,
    target_language: str
) -> Dict[str, Any]:
    """
    Convenience function for one-off translations
    
    Args:
        text: Text to translate
        source_language: Source language
        target_language: Target language
        
    Returns:
        Translation result
    """
    translator = SarvamTranslator()
    try:
        result = await translator.translate(text, source_language, target_language)
        return result
    finally:
        await translator.close()
