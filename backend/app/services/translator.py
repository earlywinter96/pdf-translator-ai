"""Compatibility wrapper for the Sarvam-only translation service."""

from app.services.hybrid_translator import HybridTranslatorV2


class UltraTranslatorService(HybridTranslatorV2):
    """Legacy name retained for callers that import this service directly."""


ImprovedTranslatorService = UltraTranslatorService
