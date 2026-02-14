#!/usr/bin/env python3
"""
Download IndicTrans2 Models
---------------------------
Downloads and caches IndicTrans2 models for offline use

Run this once before first translation:
    python scripts/download_models.py
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Models to download
MODELS = [
    {
        "name": "ai4bharat/indictrans2-en-indic-1B",
        "description": "English → Indic languages",
        "size": "~2GB"
    },
    {
        "name": "ai4bharat/indictrans2-indic-en-1B",
        "description": "Indic languages → English",
        "size": "~2GB"
    }
]

# Model storage directory
MODEL_DIR = os.getenv("INDICTRANS_MODEL_PATH", "./models/indictrans")


# ============================================================================
# DOWNLOAD FUNCTION
# ============================================================================

def download_models():
    """Download all IndicTrans2 models"""
    
    logger.info("=" * 70)
    logger.info("📥 INDICTRANS2 MODEL DOWNLOADER")
    logger.info("=" * 70)
    logger.info(f"Download location: {MODEL_DIR}")
    logger.info(f"Total size: ~4GB")
    logger.info("")
    
    # Create directory
    os.makedirs(MODEL_DIR, exist_ok=True)
    logger.info(f"✅ Created directory: {MODEL_DIR}")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        for i, model_info in enumerate(MODELS, 1):
            model_name = model_info["name"]
            description = model_info["description"]
            size = model_info["size"]
            
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"📦 MODEL {i}/{len(MODELS)}: {model_name}")
            logger.info(f"   {description}")
            logger.info(f"   Size: {size}")
            logger.info("=" * 70)
            
            # Check if already downloaded
            model_path = Path(MODEL_DIR) / model_name.replace("/", "_")
            if model_path.exists() and len(list(model_path.glob("*.bin"))) > 0:
                logger.info(f"   ✅ Model already exists at {model_path}")
                logger.info(f"   Skipping download")
                continue
            
            # Download tokenizer
            logger.info(f"   📥 Downloading tokenizer...")
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=MODEL_DIR
                )
                logger.info(f"   ✅ Tokenizer downloaded")
            except Exception as e:
                logger.error(f"   ❌ Tokenizer download failed: {e}")
                continue
            
            # Download model
            logger.info(f"   📥 Downloading model weights ({size})...")
            logger.info(f"   This may take 5-10 minutes depending on your internet speed")
            
            try:
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=MODEL_DIR
                )
                logger.info(f"   ✅ Model downloaded successfully")
                
                # Clean up model from memory
                del model
                del tokenizer
                
            except Exception as e:
                logger.error(f"   ❌ Model download failed: {e}")
                logger.error(f"   You may need to download manually")
                continue
        
        # Success summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎉 ALL MODELS DOWNLOADED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Set environment variable:")
        logger.info(f"   export INDICTRANS_MODEL_PATH={MODEL_DIR}")
        logger.info("")
        logger.info("2. Or add to your .env file:")
        logger.info(f"   INDICTRANS_MODEL_PATH={MODEL_DIR}")
        logger.info("")
        logger.info("3. Start your application:")
        logger.info("   python -m uvicorn app.main:app --reload")
        logger.info("")
        logger.info("=" * 70)
        
        return True
        
    except ImportError as e:
        logger.error("❌ Required packages not installed")
        logger.error(f"   Error: {e}")
        logger.error("")
        logger.error("Please install requirements first:")
        logger.error("   pip install -r requirements.txt")
        return False
    
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return False


# ============================================================================
# VERIFY FUNCTION
# ============================================================================

def verify_models():
    """Verify that models are downloaded and working"""
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔍 VERIFYING MODELS")
    logger.info("=" * 70)
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        for model_info in MODELS:
            model_name = model_info["name"]
            logger.info(f"\n   Checking {model_name}...")
            
            try:
                # Try to load tokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=MODEL_DIR
                )
                
                # Try to load model
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir=MODEL_DIR
                )
                
                logger.info(f"   ✅ {model_name} verified")
                
                # Clean up
                del model
                del tokenizer
                
            except Exception as e:
                logger.error(f"   ❌ {model_name} verification failed: {e}")
                return False
        
        logger.info("")
        logger.info("✅ All models verified successfully!")
        logger.info("=" * 70)
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Download IndicTrans2 models")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing models, don't download"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=MODEL_DIR,
        help=f"Model download directory (default: {MODEL_DIR})"
    )
    
    args = parser.parse_args()
    
    # Update model directory if provided
    global MODEL_DIR
    MODEL_DIR = args.model_dir
    
    if args.verify_only:
        success = verify_models()
    else:
        success = download_models()
        if success:
            verify_models()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()