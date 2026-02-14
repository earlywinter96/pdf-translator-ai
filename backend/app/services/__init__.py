# app/services/__init__.py
from .hybrid_translator import (
    HybridTranslatorV2,
    TranslationStats,
    
)

# Backward compatibility
HybridTranslator = HybridTranslatorV2

__all__ = [
    'HybridTranslatorV2',
    'HybridTranslator',
    'TranslatorService',
]