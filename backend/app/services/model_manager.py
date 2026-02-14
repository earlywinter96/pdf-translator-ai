# app/services/model_manager.py
"""
Translation Model Manager
------------------------
Manages loading and lifecycle of translation models (IndicTrans, GPT)
"""

import os
import logging
from typing import Optional, Dict
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# MODEL MANAGER
# ============================================================================

class ModelManager:
    """
    Singleton manager for translation models
    Handles lazy loading, caching, and memory management
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.models: Dict[str, any] = {}
        self.tokenizers: Dict[str, any] = {}
        self._load_lock = threading.Lock()
        
        # Configuration
        from app.config.hybrid_config import (
            INDICTRANS_MODEL_NAME,
            INDICTRANS_MODEL_PATH,
            DEVICE
        )
        
        self.model_name = INDICTRANS_MODEL_NAME
        self.model_path = INDICTRANS_MODEL_PATH
        self.device = DEVICE
        
        logger.info("📦 Model Manager initialized")
        logger.info(f"   Model: {self.model_name}")
        logger.info(f"   Device: {self.device}")
    
    def get_indictrans_model(self, direction: str = "en-indic"):
        """
        Get IndicTrans model (lazy load)
        
        Args:
            direction: 'en-indic' or 'indic-en'
            
        Returns:
            Loaded model
        """
        model_key = f"indictrans_{direction}"
        
        # Return if already loaded
        if model_key in self.models:
            logger.debug(f"   Using cached {model_key}")
            return self.models[model_key]
        
        # Load model (thread-safe)
        with self._load_lock:
            # Double-check after acquiring lock
            if model_key in self.models:
                return self.models[model_key]
            
            logger.info(f"📥 Loading {model_key} model...")
            
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                import torch
                
                # Determine model name based on direction
                if direction == "en-indic":
                    model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
                else:
                    model_name = "ai4bharat/indictrans2-indic-en-dist-200M"

                
                # Load tokenizer
                logger.info(f"   Loading tokenizer for {model_name}...")
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=self.model_path
                )
                
                # Load model
                logger.info(f"   Loading model weights...")
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=self.model_path
                )
                
                # Move to device
                if self.device == "cuda" and torch.cuda.is_available():
                    logger.info(f"   Moving model to CUDA...")
                    model = model.to("cuda")
                else:
                    logger.info(f"   Using CPU...")
                    model = model.to("cpu")
                
                # Set to eval mode
                model.eval()
                
                # Cache
                self.models[model_key] = model
                self.tokenizers[model_key] = tokenizer
                
                logger.info(f"   ✅ {model_key} loaded successfully")
                
                return model
                
            except Exception as e:
                logger.error(f"   ❌ Failed to load {model_key}: {e}")
                raise Exception(f"Model loading failed: {str(e)}")
    
    def get_tokenizer(self, direction: str = "en-indic"):
        """
        Get tokenizer for IndicTrans
        
        Args:
            direction: 'en-indic' or 'indic-en'
            
        Returns:
            Tokenizer
        """
        model_key = f"indictrans_{direction}"
        
        # Load model first (also loads tokenizer)
        if model_key not in self.tokenizers:
            self.get_indictrans_model(direction)
        
        return self.tokenizers.get(model_key)
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is loaded"""
        return model_name in self.models
    
    def unload_model(self, model_name: str):
        """
        Unload a model to free memory
        
        Args:
            model_name: Model to unload
        """
        with self._load_lock:
            if model_name in self.models:
                del self.models[model_name]
                logger.info(f"🗑️  Unloaded model: {model_name}")
            
            if model_name in self.tokenizers:
                del self.tokenizers[model_name]
    
    def unload_all(self):
        """Unload all models"""
        with self._load_lock:
            self.models.clear()
            self.tokenizers.clear()
            logger.info("🗑️  All models unloaded")
    
    def get_memory_usage(self) -> Dict:
        """
        Get memory usage statistics
        
        Returns:
            Dict with memory info
        """
        try:
            import torch
            
            stats = {
                "models_loaded": list(self.models.keys()),
                "model_count": len(self.models),
            }
            
            if torch.cuda.is_available():
                stats["cuda_memory_allocated"] = torch.cuda.memory_allocated() / 1024**2  # MB
                stats["cuda_memory_reserved"] = torch.cuda.memory_reserved() / 1024**2    # MB
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")
            return {"models_loaded": list(self.models.keys())}


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_model_manager: Optional[ModelManager] = None

def get_model_manager() -> ModelManager:
    """
    Get singleton model manager instance
    
    Returns:
        ModelManager instance
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_models_downloaded():
    """
    Ensure IndicTrans models are downloaded
    Should be called during app startup
    """
    logger.info("🔍 Checking IndicTrans models...")
    
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from app.config.hybrid_config import INDICTRANS_MODEL_PATH
        
        models_to_check = [
            "ai4bharat/indictrans2-en-indic-1B",
            "ai4bharat/indictrans2-indic-en-1B"
        ]
        
        for model_name in models_to_check:
            logger.info(f"   Checking {model_name}...")
            
            # Check if model files exist
            model_path = Path(INDICTRANS_MODEL_PATH) / model_name.replace("/", "_")
            
            if not model_path.exists():
                logger.info(f"   📥 Downloading {model_name}...")
                
                # Download tokenizer
                AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=INDICTRANS_MODEL_PATH
                )
                
                # Download model (this may take a while)
                AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=INDICTRANS_MODEL_PATH
                )
                
                logger.info(f"   ✅ {model_name} downloaded")
            else:
                logger.info(f"   ✅ {model_name} already exists")
        
        logger.info("✅ All IndicTrans models ready")
        
    except Exception as e:
        logger.error(f"❌ Model download/check failed: {e}")
        logger.warning("⚠️  Will attempt to download on first use")


def get_model_info() -> Dict:
    """
    Get information about available models
    
    Returns:
        Dict with model information
    """
    from app.config.hybrid_config import (
        INDICTRANS_MODEL_NAME,
        DEVICE,
        INDICTRANS_BATCH_SIZE
    )
    
    return {
        "indictrans": {
            "name": INDICTRANS_MODEL_NAME,
            "device": DEVICE,
            "batch_size": INDICTRANS_BATCH_SIZE,
            "languages": ["gu", "hi", "mr", "en"],
            "cost": "FREE",
            "speed": "50-100 sentences/sec"
        },
        "gpt": {
            "name": "gpt-4o-mini",
            "cost": "$0.15 per 1M input tokens",
            "use_case": "Complex content (10% of total)"
        }
    }


# ============================================================================
# CLEANUP ON SHUTDOWN
# ============================================================================

def cleanup_models():
    """Cleanup models on application shutdown"""
    try:
        manager = get_model_manager()
        manager.unload_all()
        logger.info("✅ Models cleaned up")
    except Exception as e:
        logger.error(f"❌ Model cleanup failed: {e}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test model loading
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("MODEL MANAGER TEST")
    print("=" * 70)
    
    # Get manager
    manager = get_model_manager()
    
    # Check models
    ensure_models_downloaded()
    
    # Get model info
    info = get_model_info()
    print("\n📦 Available Models:")
    for model_type, details in info.items():
        print(f"\n{model_type.upper()}:")
        for key, value in details.items():
            print(f"  {key}: {value}")
    
    # Test loading (will download if needed)
    print("\n🔄 Testing model loading...")
    try:
        model = manager.get_indictrans_model("en-indic")
        print("✅ Model loaded successfully")
        
        # Memory stats
        stats = manager.get_memory_usage()
        print(f"\n💾 Memory Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Loading failed: {e}")
    
    print("\n" + "=" * 70)