# app/config/hybrid_config.py
"""
Hybrid Translation Model Configuration
--------------------------------------
Settings for IndicTrans + GPT-4o-mini hybrid system
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# HYBRID MODEL SETTINGS
# ============================================================================

# Enable/disable hybrid model
USE_HYBRID_MODEL = os.getenv("USE_HYBRID_MODEL", "true").lower() == "true"

# Fallback to GPT if IndicTrans fails
FALLBACK_TO_GPT = os.getenv("FALLBACK_TO_GPT", "true").lower() == "true"

# Confidence threshold for IndicTrans results (0.0 - 1.0)
# If confidence < threshold, fall back to GPT
HYBRID_CONFIDENCE_THRESHOLD = float(os.getenv("HYBRID_CONFIDENCE_THRESHOLD", "0.75"))

# ============================================================================
# MODEL PATHS & SETTINGS
# ============================================================================

# IndicTrans model path
INDICTRANS_MODEL_PATH = os.getenv("INDICTRANS_MODEL_PATH", "/app/models/indictrans")

# IndicTrans model name (HuggingFace)
INDICTRANS_MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"

# Maximum characters per IndicTrans batch
MAX_CHARS_INDICTRANS = int(os.getenv("MAX_CHARS_INDICTRANS", "5000"))

# Batch size for IndicTrans (sentences per batch)
INDICTRANS_BATCH_SIZE = int(os.getenv("INDICTRANS_BATCH_SIZE", "32"))

# Device: 'cuda' for GPU, 'cpu' for CPU
DEVICE = os.getenv("DEVICE", "cpu")

# ============================================================================
# CONTENT CLASSIFICATION RULES
# ============================================================================

# Which content types use which translator
CONTENT_ROUTING: Dict[str, str] = {
    "body_text": "indictrans",      # 90% of content - fast & free
    "simple_list": "indictrans",    # Bullet points, numbering
    "headings": "gpt",              # Complex formatting
    "questions": "gpt",             # Need context understanding
    "complex": "gpt",               # Poetry, idioms, cultural references
    "tables": "gpt",                # Structured data
    "technical": "indictrans",      # Technical terms (good at this)
}

# Keywords that indicate complex content (use GPT)
COMPLEX_INDICATORS: List[str] = [
    "exercise", "activity", "question", "discuss", "analyze",
    "song", "poem", "verse", "story", "moral",
    "table", "chart", "figure", "diagram"
]

# Markers that indicate structured content
STRUCTURED_MARKERS: List[str] = [
    "[HEADING]", "[QUESTION]", "[EXERCISE]", "[SONG]",
    "[TABLE]", "[ACTIVITY]", "[/HEADING]", "[/QUESTION]"
]

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Enable translation caching
ENABLE_TRANSLATION_CACHE = os.getenv("ENABLE_TRANSLATION_CACHE", "true").lower() == "true"

# Cache backend: 'memory' or 'redis'
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory")

# Redis URL (if using Redis cache)
CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379")

# Cache TTL in seconds (1 hour)
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

# Maximum cache size (in-memory only)
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "10000"))

# ============================================================================
# PARALLEL PROCESSING
# ============================================================================

# Number of parallel translation workers
PARALLEL_WORKERS = int(os.getenv("PARALLEL_WORKERS", "8"))

# Timeout for translation requests (seconds)
TRANSLATION_TIMEOUT = int(os.getenv("TRANSLATION_TIMEOUT", "180"))

# ============================================================================
# LANGUAGE SUPPORT
# ============================================================================

# Supported language pairs for IndicTrans
INDICTRANS_SUPPORTED_PAIRS = {
    # Source -> Target
    ("gujarati", "english"): "gu-en",
    ("english", "gujarati"): "en-gu",
    ("hindi", "english"): "hi-en",
    ("english", "hindi"): "en-hi",
    ("marathi", "english"): "mr-en",
    ("english", "marathi"): "en-mr",
}

# Language codes mapping
LANGUAGE_CODES = {
    "gujarati": "gu",
    "hindi": "hi",
    "marathi": "mr",
    "english": "en",
}

# ============================================================================
# QUALITY SETTINGS
# ============================================================================

# Minimum translation quality score (0.0 - 1.0)
MIN_QUALITY_SCORE = float(os.getenv("MIN_QUALITY_SCORE", "0.70"))

# Enable quality checking
ENABLE_QUALITY_CHECK = os.getenv("ENABLE_QUALITY_CHECK", "true").lower() == "true"

# Quality check method: 'bleu', 'meteor', 'backtranslation'
QUALITY_CHECK_METHOD = os.getenv("QUALITY_CHECK_METHOD", "backtranslation")

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

# Target: Use GPT for only X% of content
GPT_USAGE_TARGET = float(os.getenv("GPT_USAGE_TARGET", "0.10"))  # 10%

# Track cost per translation
TRACK_COSTS = os.getenv("TRACK_COSTS", "true").lower() == "true"

# Cost per 1K tokens (USD)
GPT_COST_PER_1K_INPUT = 0.00015
GPT_COST_PER_1K_OUTPUT = 0.00060
INDICTRANS_COST = 0.0  # Free!

# ============================================================================
# LOGGING & MONITORING
# ============================================================================

# Log translation decisions
LOG_ROUTING_DECISIONS = os.getenv("LOG_ROUTING_DECISIONS", "true").lower() == "true"

# Log performance metrics
LOG_PERFORMANCE = os.getenv("LOG_PERFORMANCE", "true").lower() == "true"

# Save translation examples for analysis
SAVE_TRANSLATION_SAMPLES = os.getenv("SAVE_TRANSLATION_SAMPLES", "false").lower() == "true"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_model_for_content_type(content_type: str) -> str:
    """
    Get the best translation model for a content type
    
    Args:
        content_type: Type of content (body_text, heading, etc.)
        
    Returns:
        Model name: 'indictrans' or 'gpt'
    """
    return CONTENT_ROUTING.get(content_type, "indictrans")


def is_complex_content(text: str) -> bool:
    """
    Check if text is complex and needs GPT
    
    Args:
        text: Text to check
        
    Returns:
        True if complex (needs GPT)
    """
    text_lower = text.lower()
    
    # Check for structured markers
    if any(marker.lower() in text_lower for marker in STRUCTURED_MARKERS):
        return True
    
    # Check for complex indicators
    if any(indicator in text_lower for indicator in COMPLEX_INDICATORS):
        return True
    
    # Check text characteristics
    # Very short text might be headings
    if len(text.strip()) < 50 and text.isupper():
        return True
    
    # Contains special formatting
    if text.count("**") > 2 or text.count("__") > 2:
        return True
    
    return False


def get_language_pair_code(source_lang: str, target_lang: str) -> str:
    """
    Get IndicTrans language pair code
    
    Args:
        source_lang: Source language name
        target_lang: Target language name
        
    Returns:
        Language pair code (e.g., 'gu-en')
    """
    pair = (source_lang.lower(), target_lang.lower())
    return INDICTRANS_SUPPORTED_PAIRS.get(pair, "")


def is_supported_by_indictrans(source_lang: str, target_lang: str) -> bool:
    """
    Check if language pair is supported by IndicTrans
    
    Args:
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        True if supported
    """
    pair = (source_lang.lower(), target_lang.lower())
    return pair in INDICTRANS_SUPPORTED_PAIRS


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_hybrid_config():
    """Validate hybrid configuration on startup"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("🔧 HYBRID TRANSLATION CONFIGURATION")
    logger.info("=" * 70)
    
    # Basic settings
    logger.info(f"Hybrid Mode: {'ENABLED' if USE_HYBRID_MODEL else 'DISABLED'}")
    logger.info(f"Device: {DEVICE.upper()}")
    logger.info(f"Confidence Threshold: {HYBRID_CONFIDENCE_THRESHOLD:.0%}")
    logger.info(f"Fallback to GPT: {'YES' if FALLBACK_TO_GPT else 'NO'}")
    
    # Model settings
    logger.info(f"\n📦 Model Settings:")
    logger.info(f"  IndicTrans Model: {INDICTRANS_MODEL_NAME}")
    logger.info(f"  Model Path: {INDICTRANS_MODEL_PATH}")
    logger.info(f"  Batch Size: {INDICTRANS_BATCH_SIZE}")
    logger.info(f"  Max Chars: {MAX_CHARS_INDICTRANS}")
    
    # Performance
    logger.info(f"\n⚡ Performance:")
    logger.info(f"  Parallel Workers: {PARALLEL_WORKERS}")
    logger.info(f"  Cache Enabled: {'YES' if ENABLE_TRANSLATION_CACHE else 'NO'}")
    logger.info(f"  Cache Backend: {CACHE_BACKEND.upper()}")
    
    # Cost optimization
    logger.info(f"\n💰 Cost Optimization:")
    logger.info(f"  Target GPT Usage: {GPT_USAGE_TARGET:.0%}")
    logger.info(f"  IndicTrans Cost: FREE")
    logger.info(f"  GPT Cost (1K in): ${GPT_COST_PER_1K_INPUT:.5f}")
    logger.info(f"  GPT Cost (1K out): ${GPT_COST_PER_1K_OUTPUT:.5f}")
    
    # Quality
    logger.info(f"\n✅ Quality:")
    logger.info(f"  Min Quality Score: {MIN_QUALITY_SCORE:.0%}")
    logger.info(f"  Quality Check: {'ENABLED' if ENABLE_QUALITY_CHECK else 'DISABLED'}")
    logger.info(f"  Method: {QUALITY_CHECK_METHOD.upper()}")
    
    # Supported languages
    logger.info(f"\n🌍 Supported Language Pairs:")
    for (src, tgt), code in INDICTRANS_SUPPORTED_PAIRS.items():
        logger.info(f"  {src.title()} ↔ {tgt.title()} ({code})")
    
    logger.info("=" * 70)
    
    # Warnings
    if not USE_HYBRID_MODEL:
        logger.warning("⚠️  Hybrid mode DISABLED - using GPT-only pipeline")
    
    if DEVICE == "cuda" and not check_cuda_available():
        logger.warning("⚠️  CUDA requested but not available - falling back to CPU")
    
    if HYBRID_CONFIDENCE_THRESHOLD < 0.5:
        logger.warning("⚠️  Low confidence threshold - may use GPT too often")


def check_cuda_available() -> bool:
    """Check if CUDA is available"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

__all__ = [
    'USE_HYBRID_MODEL',
    'FALLBACK_TO_GPT',
    'HYBRID_CONFIDENCE_THRESHOLD',
    'INDICTRANS_MODEL_PATH',
    'INDICTRANS_MODEL_NAME',
    'MAX_CHARS_INDICTRANS',
    'INDICTRANS_BATCH_SIZE',
    'DEVICE',
    'CONTENT_ROUTING',
    'COMPLEX_INDICATORS',
    'STRUCTURED_MARKERS',
    'ENABLE_TRANSLATION_CACHE',
    'CACHE_BACKEND',
    'PARALLEL_WORKERS',
    'TRANSLATION_TIMEOUT',
    'INDICTRANS_SUPPORTED_PAIRS',
    'LANGUAGE_CODES',
    'MIN_QUALITY_SCORE',
    'ENABLE_QUALITY_CHECK',
    'GPT_USAGE_TARGET',
    'get_model_for_content_type',
    'is_complex_content',
    'get_language_pair_code',
    'is_supported_by_indictrans',
    'validate_hybrid_config',
]