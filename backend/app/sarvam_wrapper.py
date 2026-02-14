"""
Sarvam AI Translation Wrapper - IMPROVED VERSION
=================================================
Enhanced wrapper with better error handling, retry logic, and validation
"""

import os
import logging
import time
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_API_URL = "https://api.sarvam.ai/translate"
SARVAM_MODEL = "sarvam-translate:v1"

# Cost per 1000 characters (in INR)
COST_PER_1K_CHARS = 1.40

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
BACKOFF_MULTIPLIER = 2.0

# Request timeout
REQUEST_TIMEOUT = 30.0

# Supported languages
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
    "en": "en-IN"
}


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
    
    # Check if already in correct format
    if normalized in SUPPORTED_LANGUAGES.values():
        return normalized
    
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
        # Validate inputs
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