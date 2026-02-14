# app/models/translation_cache.py
"""
Translation Cache
----------------
In-memory cache for frequently translated phrases
"""

import logging
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

# ============================================================================
# TRANSLATION CACHE
# ============================================================================

class TranslationCache:
    """
    Simple in-memory translation cache
    LRU eviction when size limit reached
    """
    
    def __init__(self, max_size: int = 10000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.cache: Dict[str, dict] = {}
        self._lock = threading.Lock()
        
        logger.info(f"💾 Translation Cache initialized (max: {max_size}, TTL: {ttl_hours}h)")
    
    def get(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """
        Get cached translation
        
        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Cached translation or None
        """
        key = self._make_key(text, source_lang, target_lang)
        
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if datetime.now() - entry['timestamp'] > self.ttl:
                    del self.cache[key]
                    return None
                
                # Update access time (for LRU)
                entry['last_access'] = datetime.now()
                entry['hit_count'] += 1
                
                logger.debug(f"   💾 Cache HIT")
                return entry['translation']
        
        logger.debug(f"   ❌ Cache MISS")
        return None
    
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str
    ):
        """
        Cache a translation
        
        Args:
            text: Source text
            source_lang: Source language
            target_lang: Target language
            translation: Translated text
        """
        key = self._make_key(text, source_lang, target_lang)
        
        with self._lock:
            # Evict old entries if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Add to cache
            self.cache[key] = {
                'translation': translation,
                'timestamp': datetime.now(),
                'last_access': datetime.now(),
                'hit_count': 0
            }
    
    def _make_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key"""
        key_str = f"{source_lang}:{target_lang}:{text}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['last_access']
        )
        
        del self.cache[lru_key]
        logger.debug("   🗑️  Evicted LRU cache entry")
    
    def clear(self):
        """Clear all cache"""
        with self._lock:
            self.cache.clear()
        logger.info("💾 Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total_hits = sum(entry['hit_count'] for entry in self.cache.values())
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'total_hits': total_hits,
                'utilization': f"{len(self.cache) / self.max_size * 100:.1f}%"
            }


# ============================================================================
# SINGLETON
# ============================================================================

_cache: Optional[TranslationCache] = None

def get_cache() -> TranslationCache:
    """Get singleton cache instance"""
    global _cache
    if _cache is None:
        from app.config.hybrid_config import MAX_CACHE_SIZE, CACHE_TTL
        _cache = TranslationCache(
            max_size=MAX_CACHE_SIZE,
            ttl_hours=CACHE_TTL // 3600
        )
    return _cache