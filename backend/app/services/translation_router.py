# app/services/translation_router.py
"""
Translation Router
-----------------
Intelligently routes content to the best translation model:
- Body text → IndicTrans (90% - fast & free)
- Complex content → GPT-4o-mini (10% - quality)
"""

import logging
from typing import Tuple, Dict, List
from dataclasses import dataclass

from app.services.content_classifier import ContentClassifier, ContentType
from app.config.hybrid_config import (
    HYBRID_CONFIDENCE_THRESHOLD,
    FALLBACK_TO_GPT,
    GPT_USAGE_TARGET,
    LOG_ROUTING_DECISIONS
)

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTING DECISION
# ============================================================================

@dataclass
class RoutingDecision:
    """Decision on which model to use"""
    model: str  # 'indictrans' or 'gpt'
    reason: str
    content_type: str
    confidence: float
    use_cache: bool = True


# ============================================================================
# TRANSLATION ROUTER
# ============================================================================

class TranslationRouter:
    """
    Routes translation requests to the optimal model
    """
    
    def __init__(self):
        self.classifier = ContentClassifier()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'indictrans_count': 0,
            'gpt_count': 0,
            'cache_hits': 0,
            'fallback_count': 0
        }
        
        logger.info("🧭 Translation Router initialized")
        logger.info(f"   Target GPT usage: {GPT_USAGE_TARGET:.0%}")
        logger.info(f"   Confidence threshold: {HYBRID_CONFIDENCE_THRESHOLD:.0%}")
    
    def route(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        force_model: str = None
    ) -> RoutingDecision:
        """
        Decide which model to use for translation
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            force_model: Force specific model (for testing)
            
        Returns:
            RoutingDecision
        """
        self.stats['total_requests'] += 1
        
        # Force model if specified
        if force_model:
            self._update_stats(force_model)
            return RoutingDecision(
                model=force_model,
                reason="Forced by caller",
                content_type="unknown",
                confidence=1.0
            )
        
        # Classify content
        content_type = self.classifier.classify_text(text)
        
        # Decision logic
        decision = self._make_routing_decision(text, content_type, source_lang, target_lang)
        
        # Update statistics
        self._update_stats(decision.model)
        
        # Log decision
        if LOG_ROUTING_DECISIONS:
            self._log_decision(text, decision)
        
        return decision
    
    def _make_routing_decision(
        self,
        text: str,
        content_type: str,
        source_lang: str,
        target_lang: str
    ) -> RoutingDecision:
        """
        Make routing decision based on content analysis
        
        Args:
            text: Text to translate
            content_type: Classified content type
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            RoutingDecision
        """
        # Rule 1: Complex content types → GPT
        complex_types = [
            ContentType.HEADING,
            ContentType.QUESTION,
            ContentType.COMPLEX,
            'song',
            'exercise'
        ]
        
        if content_type in complex_types:
            return RoutingDecision(
                model='gpt',
                reason=f"Complex content type: {content_type}",
                content_type=content_type,
                confidence=0.90
            )
        
        # Rule 2: Very short text (headings) → GPT
        if len(text.strip()) < 50 and text.isupper():
            return RoutingDecision(
                model='gpt',
                reason="Short uppercase text (likely heading)",
                content_type=content_type,
                confidence=0.85
            )
        
        # Rule 3: Questions → GPT
        if '?' in text and text.count('?') >= 2:
            return RoutingDecision(
                model='gpt',
                reason="Multiple questions detected",
                content_type=content_type,
                confidence=0.85
            )
        
        # Rule 4: Check if we're over GPT usage target
        gpt_usage_rate = self._get_gpt_usage_rate()
        if gpt_usage_rate > GPT_USAGE_TARGET * 1.5:  # 50% over target
            logger.warning(f"⚠️  GPT usage too high ({gpt_usage_rate:.0%}), using IndicTrans")
            return RoutingDecision(
                model='indictrans',
                reason=f"GPT usage over target ({gpt_usage_rate:.0%})",
                content_type=content_type,
                confidence=0.70
            )
        
        # Rule 5: Body text, lists, technical → IndicTrans
        fast_types = [
            ContentType.BODY_TEXT,
            ContentType.LIST,
            ContentType.TECHNICAL
        ]
        
        if content_type in fast_types:
            return RoutingDecision(
                model='indictrans',
                reason=f"Standard content type: {content_type}",
                content_type=content_type,
                confidence=0.85
            )
        
        # Default: IndicTrans (safer, faster, free)
        return RoutingDecision(
            model='indictrans',
            reason="Default routing to IndicTrans",
            content_type=content_type,
            confidence=0.75
        )
    
    def route_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[RoutingDecision]:
        """
        Route multiple texts
        
        Args:
            texts: List of texts
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            List of routing decisions
        """
        decisions = []
        
        for text in texts:
            decision = self.route(text, source_lang, target_lang)
            decisions.append(decision)
        
        return decisions
    
    def should_fallback_to_gpt(
        self,
        indictrans_result: str,
        confidence: float
    ) -> bool:
        """
        Decide if we should fall back to GPT after IndicTrans attempt
        
        Args:
            indictrans_result: Translation from IndicTrans
            confidence: Confidence score
            
        Returns:
            True if should fallback
        """
        if not FALLBACK_TO_GPT:
            return False
        
        # Check confidence threshold
        if confidence < HYBRID_CONFIDENCE_THRESHOLD:
            logger.info(f"   ⚠️  Low confidence ({confidence:.2%}), considering GPT fallback")
            return True
        
        # Check if result is empty or too short
        if not indictrans_result.strip() or len(indictrans_result) < 10:
            logger.info("   ⚠️  Result too short, falling back to GPT")
            return True
        
        # Check if result looks corrupted (too repetitive)
        words = indictrans_result.split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                logger.info("   ⚠️  Result too repetitive, falling back to GPT")
                return True
        
        return False
    
    def _update_stats(self, model: str):
        """Update routing statistics"""
        if model == 'indictrans':
            self.stats['indictrans_count'] += 1
        elif model == 'gpt':
            self.stats['gpt_count'] += 1
    
    def _get_gpt_usage_rate(self) -> float:
        """Get current GPT usage rate"""
        total = self.stats['total_requests']
        if total == 0:
            return 0.0
        return self.stats['gpt_count'] / total
    
    def _log_decision(self, text: str, decision: RoutingDecision):
        """Log routing decision"""
        text_preview = text[:50] + "..." if len(text) > 50 else text
        logger.debug(f"🧭 Route: {decision.model.upper()}")
        logger.debug(f"   Text: {text_preview}")
        logger.debug(f"   Type: {decision.content_type}")
        logger.debug(f"   Reason: {decision.reason}")
        logger.debug(f"   Confidence: {decision.confidence:.2%}")
    
    def get_statistics(self) -> Dict:
        """
        Get routing statistics
        
        Returns:
            Statistics dictionary
        """
        total = self.stats['total_requests']
        
        if total == 0:
            return {
                'total_requests': 0,
                'indictrans_rate': 0.0,
                'gpt_rate': 0.0,
                'target_gpt_rate': GPT_USAGE_TARGET,
                'status': 'No requests yet'
            }
        
        indictrans_rate = self.stats['indictrans_count'] / total
        gpt_rate = self.stats['gpt_count'] / total
        
        # Status message
        if gpt_rate <= GPT_USAGE_TARGET:
            status = "✅ Within target"
        elif gpt_rate <= GPT_USAGE_TARGET * 1.2:
            status = "⚠️  Slightly over target"
        else:
            status = "❌ Significantly over target"
        
        return {
            'total_requests': total,
            'indictrans_count': self.stats['indictrans_count'],
            'gpt_count': self.stats['gpt_count'],
            'cache_hits': self.stats['cache_hits'],
            'fallback_count': self.stats['fallback_count'],
            'indictrans_rate': indictrans_rate,
            'gpt_rate': gpt_rate,
            'target_gpt_rate': GPT_USAGE_TARGET,
            'status': status,
            'cost_savings': f"{(1 - gpt_rate) * 100:.0f}% cost reduction"
        }
    
    def reset_statistics(self):
        """Reset routing statistics"""
        self.stats = {
            'total_requests': 0,
            'indictrans_count': 0,
            'gpt_count': 0,
            'cache_hits': 0,
            'fallback_count': 0
        }
        logger.info("📊 Statistics reset")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_router: TranslationRouter = None

def get_router() -> TranslationRouter:
    """Get singleton router instance"""
    global _router
    if _router is None:
        _router = TranslationRouter()
    return _router


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def route_translation(
    text: str,
    source_lang: str,
    target_lang: str
) -> str:
    """
    Quick routing decision
    
    Args:
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        Model name: 'indictrans' or 'gpt'
    """
    router = get_router()
    decision = router.route(text, source_lang, target_lang)
    return decision.model


def get_routing_stats() -> Dict:
    """Get current routing statistics"""
    router = get_router()
    return router.get_statistics()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("TRANSLATION ROUTER TEST")
    print("=" * 70)
    
    # Create router
    router = get_router()
    
    # Test cases
    test_cases = [
        ("This is a regular paragraph with some text.", "Body text"),
        ("CHAPTER 1: INTRODUCTION", "Heading"),
        ("What is the capital of India? Explain your answer.", "Question"),
        ("• First point\n• Second point\n• Third point", "List"),
        ("[SONG]\nRow row row your boat\n[/SONG]", "Song"),
    ]
    
    print("\n🧭 Routing Decisions:")
    print("=" * 70)
    
    for text, description in test_cases:
        decision = router.route(text, "gujarati", "english")
        
        text_preview = text[:40] + "..." if len(text) > 40 else text
        
        print(f"\n{description}:")
        print(f"  Text: {text_preview}")
        print(f"  Model: {decision.model.upper()} {'🚀' if decision.model == 'indictrans' else '🎯'}")
        print(f"  Reason: {decision.reason}")
        print(f"  Confidence: {decision.confidence:.0%}")
    
    # Statistics
    print("\n" + "=" * 70)
    print("📊 Routing Statistics:")
    print("=" * 70)
    
    stats = router.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)