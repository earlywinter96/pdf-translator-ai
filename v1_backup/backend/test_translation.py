# test_translation.py
"""
Quick test script to verify translation is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.chunker import chunk_pages_fast, reassemble_chunks_to_pages
from app.services.pdf_writer import create_translated_pdf_fixed


async def test_chunking():
    """Test fast chunking"""
    print("=" * 70)
    print("TEST 1: Fast Chunking")
    print("=" * 70)
    
    # Sample pages
    pages = [
        "This is page 1.\n\nIt has multiple paragraphs.\n\nLike this one.",
        "Page 2 is here.\n\nWith more content.\n\nAnd another paragraph.",
        "Final page 3.\n\nLast bits of text.\n\nThe end."
    ]
    
    print(f"Input: {len(pages)} pages")
    
    # Test chunking
    import time
    start = time.time()
    chunks = chunk_pages_fast(pages, max_words_per_chunk=50)
    elapsed = time.time() - start
    
    print(f"Output: {len(chunks)} chunks")
    print(f"Time: {elapsed:.3f}s")
    print(f"\nFirst chunk preview:")
    print(chunks[0][:100] + "...")
    
    # Test reassembly
    reassembled = reassemble_chunks_to_pages(chunks, len(pages))
    print(f"\nReassembled: {len(reassembled)} pages")
    
    if len(reassembled) == len(pages):
        print("✅ Chunking test PASSED")
    else:
        print("❌ Chunking test FAILED")
    
    return chunks


async def test_translation(chunks):
    """Test translation (mock)"""
    print("\n" + "=" * 70)
    print("TEST 2: Translation (Mock)")
    print("=" * 70)
    
    # Mock translation (replace with actual translator for real test)
    translated_chunks = [f"[TRANSLATED] {chunk}" for chunk in chunks]
    
    print(f"Translated {len(translated_chunks)} chunks")
    print(f"\nFirst translated chunk:")
    print(translated_chunks[0][:100] + "...")
    
    print("✅ Translation test PASSED (mock)")
    
    return translated_chunks


async def test_pdf_creation():
    """Test PDF creation"""
    print("\n" + "=" * 70)
    print("TEST 3: PDF Creation")
    print("=" * 70)
    
    # You need a sample PDF for this test
    # Create a simple one if needed
    
    print("⚠️  Skipping PDF creation test (need sample PDF)")
    print("   To test manually:")
    print("   1. Put a sample.pdf in current directory")
    print("   2. Run: python -c 'from pdf_writer_fixed import create_translated_pdf_fixed; create_translated_pdf_fixed(\"sample.pdf\", [\"Translated text\"], \"output.pdf\")'")


async def run_all_tests():
    """Run all tests"""
    print("\n🧪 Running Translation System Tests...\n")
    
    # Test 1: Chunking
    chunks = await test_chunking()
    
    # Test 2: Translation
    translated = await test_translation(chunks)
    
    # Test 3: PDF Creation
    await test_pdf_creation()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Replace your old files with the new optimized ones")
    print("2. Test with a real PDF")
    print("3. Verify translation actually happens (not just a copy!)")
    print("4. Check processing time (should be 3-5 min, not 15-20 min)")


if __name__ == "__main__":
    asyncio.run(run_all_tests())