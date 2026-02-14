# app/models/translation_stats.py
"""
Translation Statistics Tracker
------------------------------
Track usage, costs, and performance of hybrid translation
"""

import json
import logging
from typing import Dict
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

# ============================================================================
# STATISTICS TRACKER
# ============================================================================

class TranslationStats:
    """Track translation statistics"""
    
    def __init__(self, stats_file: str = "translation_stats.json"):
        self.stats_file = stats_file
        self._lock = threading.Lock()
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """Load stats from file"""
        if Path(self.stats_file).exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")
        
        return self._init_stats()
    
    def _init_stats(self) -> Dict:
        """Initialize empty stats"""
        return {
            'total_translations': 0,
            'indictrans_count': 0,
            'gpt_count': 0,
            'cache_hits': 0,
            'fallbacks': 0,
            'total_cost_inr': 0.0,
            'total_chars': 0,
            'daily_stats': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def record_translation(
        self,
        model: str,
        chars: int,
        cost: float = 0.0,
        from_cache: bool = False
    ):
        """Record a translation"""
        with self._lock:
            self.stats['total_translations'] += 1
            self.stats['total_chars'] += chars
            self.stats['total_cost_inr'] += cost
            
            if from_cache:
                self.stats['cache_hits'] += 1
            elif model == 'indictrans':
                self.stats['indictrans_count'] += 1
            elif model == 'gpt':
                self.stats['gpt_count'] += 1
            
            # Daily stats
            today = datetime.now().date().isoformat()
            if today not in self.stats['daily_stats']:
                self.stats['daily_stats'][today] = {
                    'translations': 0,
                    'indictrans': 0,
                    'gpt': 0,
                    'cost_inr': 0.0
                }
            
            self.stats['daily_stats'][today]['translations'] += 1
            if model == 'indictrans':
                self.stats['daily_stats'][today]['indictrans'] += 1
            elif model == 'gpt':
                self.stats['daily_stats'][today]['gpt'] += 1
            self.stats['daily_stats'][today]['cost_inr'] += cost
            
            self.stats['last_updated'] = datetime.now().isoformat()
            
            self._save_stats()
    
    def record_fallback(self):
        """Record a fallback from IndicTrans to GPT"""
        with self._lock:
            self.stats['fallbacks'] += 1
            self._save_stats()
    
    def get_summary(self) -> Dict:
        """Get statistics summary"""
        with self._lock:
            total = self.stats['total_translations']
            if total == 0:
                return {
                    'total_translations': 0,
                    'cost_savings': '0%',
                    'message': 'No translations yet'
                }
            
            indictrans_pct = (self.stats['indictrans_count'] / total) * 100
            gpt_pct = (self.stats['gpt_count'] / total) * 100
            cache_pct = (self.stats['cache_hits'] / total) * 100
            
            return {
                'total_translations': total,
                'indictrans_percentage': f"{indictrans_pct:.1f}%",
                'gpt_percentage': f"{gpt_pct:.1f}%",
                'cache_hit_rate': f"{cache_pct:.1f}%",
                'total_cost_inr': f"₹{self.stats['total_cost_inr']:.2f}",
                'total_chars': self.stats['total_chars'],
                'cost_savings': f"{indictrans_pct:.0f}%",
                'fallback_count': self.stats['fallbacks']
            }
    
    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")


# ============================================================================
# SINGLETON
# ============================================================================

_stats: TranslationStats = None

def get_stats() -> TranslationStats:
    """Get singleton stats instance"""
    global _stats
    if _stats is None:
        _stats = TranslationStats()
    return _stats