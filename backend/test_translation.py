#!/usr/bin/env python3
"""
LipiTranslate V2 - System Test Script
======================================
Tests Sarvam AI integration and translation pipeline
"""

import sys
import os
import logging
import asyncio
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_environment():
    """Test 1: Check environment variables"""
    print("\n" + "=" * 70)
    print("TEST 1: Environment Configuration")
    print("=" * 70)
    
    required_vars = {
        'SARVAM_API_KEY': 'Sarvam AI API Key',
        'OPENAI_API_KEY': 'OpenAI API Key',
    }
    
    optional_vars = {
        'SARVAM_MODEL': 'Sarvam Model',
        'TRANSLATION_MODEL': 'OpenAI Model',
        'FALLBACK_TO_OPENAI': 'Fallback Setting',
    }
    
    all_good = True
    
    print("\n✅ Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✓ {description}: {masked}")
        else:
            print(f"   ✗ {description}: NOT SET")
            all_good = False
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var, 'Not set')
        print(f"   • {description}: {value}")
    
    if all_good:
        print("\n✅ Environment configuration: PASSED")
    else:
        print("\n❌ Environment configuration: FAILED")
        print("\nPlease set missing variables in .env file")
    
    return all_good


def test_imports():
    """Test 2: Check if all modules can be imported"""
    print("\n" + "=" * 70)
    print("TEST 2: Module Imports")
    print("=" * 70)
    
    modules = [
        ('fastapi', 'FastAPI Framework'),
        ('requests', 'HTTP Requests'),
        ('openai', 'OpenAI Client'),
        ('razorpay', 'Razorpay Client'),
        ('fitz', 'PyMuPDF'),
        ('reportlab', 'ReportLab PDF'),
        ('PIL', 'Pillow Image Processing'),
        ('pytesseract', 'Tesseract OCR'),
    ]
    
    all_good = True
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"   ✓ {description}")
        except ImportError as e:
            print(f"   ✗ {description}: {e}")
            all_good = False
    
    if all_good:
        print("\n✅ Module imports: PASSED")
    else:
        print("\n❌ Module imports: FAILED")
        print("\nRun: pip install -r requirements.txt")
    
    return all_good


def test_sarvam_api():
    """Test 3: Test Sarvam AI API connection"""
    print("\n" + "=" * 70)
    print("TEST 3: Sarvam AI API")
    print("=" * 70)
    
    try:
        from app.sarvam_wrapper import get_sarvam_client
        
        client = get_sarvam_client()
        print("   ✓ Sarvam client initialized")
        
        # Test translation
        print("\n   Testing translation...")
        test_text = "Hello, how are you?"
        result, confidence, metadata = client.translate(
            test_text,
            "english",
            "gujarati",
            "formal"
        )
        
        if result and confidence > 0.5:
            print(f"   ✓ Translation successful")
            print(f"   • Input: {test_text}")
            print(f"   • Output: {result}")
            print(f"   • Confidence: {confidence:.2%}")
            print(f"   • Cost: ₹{metadata.get('cost_inr', 0):.4f}")
            print("\n✅ Sarvam AI API: PASSED")
            return True
        else:
            print(f"   ✗ Translation failed or low confidence")
            print("\n❌ Sarvam AI API: FAILED")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n❌ Sarvam AI API: FAILED")
        return False


def test_openai_api():
    """Test 4: Test OpenAI API connection"""
    print("\n" + "=" * 70)
    print("TEST 4: OpenAI API")
    print("=" * 70)
    
    try:
        from app.openai_wrapper import get_openai_client
        
        client = get_openai_client()
        print("   ✓ OpenAI client initialized")
        
        # Test translation
        print("\n   Testing translation...")
        result = client.translate_text(
            text="Hello",
            source_language="english",
            target_language="gujarati",
            mode="general"
        )
        
        if result and result.get('text'):
            print(f"   ✓ Translation successful")
            print(f"   • Output: {result['text']}")
            print(f"   • Tokens: {result.get('tokens', 0)}")
            print(f"   • Cost: ₹{result.get('cost', 0):.4f}")
            print("\n✅ OpenAI API: PASSED")
            return True
        else:
            print(f"   ✗ Translation failed")
            print("\n❌ OpenAI API: FAILED")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n❌ OpenAI API: FAILED")
        return False


async def test_hybrid_translator():
    """Test 5: Test hybrid translation system"""
    print("\n" + "=" * 70)
    print("TEST 5: Hybrid Translation System")
    print("=" * 70)
    
    try:
        from app.services.hybrid_translator import HybridTranslatorV2
        
        translator = HybridTranslatorV2(
            source_language="gujarati",
            target_language="english",
            mode="general"
        )
        print("   ✓ Hybrid translator initialized")
        
        # Test with multiple chunks
        print("\n   Testing chunk translation...")
        test_chunks = [
            "આ એક સામાન્ય વાક્ય છે.",
            "તમે કેમ છો?",
            "આજે હવામાન સારું છે."
        ]
        
        results = await translator.translate_chunks(test_chunks)
        
        if len(results) == len(test_chunks):
            print(f"   ✓ Translated {len(results)} chunks")
            
            stats = translator.get_statistics()
            print(f"\n   📊 Statistics:")
            print(f"   • Sarvam AI: {stats['sarvam_used']} chunks")
            print(f"   • OpenAI: {stats['openai_used']} chunks")
            print(f"   • Total cost: ₹{stats['total_cost_inr']:.4f}")
            
            print("\n✅ Hybrid Translation: PASSED")
            return True
        else:
            print(f"   ✗ Translation failed")
            print("\n❌ Hybrid Translation: FAILED")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        logger.exception("Hybrid translation test failed")
        print("\n❌ Hybrid Translation: FAILED")
        return False


def test_directories():
    """Test 6: Check required directories"""
    print("\n" + "=" * 70)
    print("TEST 6: Directory Structure")
    print("=" * 70)
    
    dirs = ['uploads', 'outputs', 'visualizations']
    all_good = True
    
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   ✗ {dir_name}/ - creating...")
            try:
                os.makedirs(dir_name)
                print(f"      ✓ Created")
            except Exception as e:
                print(f"      ✗ Failed: {e}")
                all_good = False
    
    if all_good:
        print("\n✅ Directory structure: PASSED")
    else:
        print("\n❌ Directory structure: FAILED")
    
    return all_good


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 LIPITRANSLATE V2 - SYSTEM TESTS")
    print("=" * 70)
    
    results = {
        'Environment': test_environment(),
        'Imports': test_imports(),
        'Directories': test_directories(),
    }
    
    # Only run API tests if basics pass
    if results['Environment'] and results['Imports']:
        results['Sarvam API'] = test_sarvam_api()
        results['OpenAI API'] = test_openai_api()
        results['Hybrid Translator'] = await test_hybrid_translator()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\nYour system is ready for production!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("=" * 70)
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)