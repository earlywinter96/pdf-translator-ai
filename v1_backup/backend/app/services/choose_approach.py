# choose_approach.py
"""
Helper script to choose the best PDF translation approach.

Run this to determine which method is best for your PDFs.
"""

import PyPDF2
import fitz
import sys


def analyze_pdf(pdf_path: str):
    """
    Analyze PDF and recommend best translation approach.
    """
    print("=" * 70)
    print(f"📄 Analyzing: {pdf_path}")
    print("=" * 70)
    
    # Open with PyPDF2
    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        page_count = len(pdf_reader.pages)
        
        # Extract text from first page
        first_page_text = pdf_reader.pages[0].extract_text()
        
    # Open with PyMuPDF for detailed analysis
    doc = fitz.open(pdf_path)
    first_page = doc[0]
    
    # Get images
    images = first_page.get_images()
    
    # Get text blocks
    text_blocks = first_page.get_text("dict")["blocks"]
    text_block_count = sum(1 for b in text_blocks if b.get("type") == 0)
    
    # Calculate text density
    text_length = len(first_page_text)
    page_area = first_page.rect.width * first_page.rect.height
    text_density = text_length / (page_area / 10000) if page_area > 0 else 0
    
    doc.close()
    
    # Print analysis
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   Pages: {page_count}")
    print(f"   Images on page 1: {len(images)}")
    print(f"   Text blocks on page 1: {text_block_count}")
    print(f"   Text length on page 1: {text_length} chars")
    print(f"   Text density: {text_density:.2f}")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATION:")
    print("=" * 70)
    
    if text_length < 50:
        print("⚠️  PDF appears to be SCANNED or IMAGE-BASED")
        print("\n✅ BEST APPROACH: Use overlay method")
        print("   File: pdf_simple_overlay.py")
        print("   Function: create_overlay_pdf()")
        print("\n   Why: Scanned PDFs need OCR, overlay preserves images perfectly")
        
    elif len(images) > text_block_count * 2:
        print("📸 PDF is IMAGE-HEAVY")
        print("\n✅ BEST APPROACH: Use fixed writer with image preservation")
        print("   File: pdf_writer_fixed.py")
        print("   Function: create_translated_pdf_fixed()")
        print("\n   Why: Balances image preservation with text replacement")
        
    elif text_density > 5:
        print("📝 PDF is TEXT-HEAVY")
        print("\n✅ BEST APPROACH: Use optimized fast method")
        print("   File: main_optimized.py")
        print("   Function: process_translation_optimized()")
        print("\n   Why: Fast processing, good text replacement")
        
    else:
        print("📄 PDF is MIXED CONTENT")
        print("\n✅ BEST APPROACH: Use fixed writer")
        print("   File: pdf_writer_fixed.py")
        print("   Function: create_translated_pdf_fixed()")
        print("\n   Why: Best balance for mixed content")
    
    print("=" * 70)
    
    # Additional recommendations
    print("\n🎯 ADDITIONAL OPTIONS:")
    print("\n1. For COMPARISON/LEARNING:")
    print("   Use: create_sidebyside_pdf() from pdf_simple_overlay.py")
    print("   Shows original and translation side-by-side")
    
    print("\n2. For 100% VISUAL PRESERVATION:")
    print("   Use: create_overlay_pdf() from pdf_simple_overlay.py")
    print("   Keeps original intact, adds invisible text layer")
    
    print("\n3. For MAXIMUM SPEED:")
    print("   Use: main_optimized.py with chunk_pages_fast()")
    print("   10x faster chunking, parallel translation")
    
    print("\n" + "=" * 70)


def compare_approaches():
    """
    Show comparison table of all approaches.
    """
    print("\n" + "=" * 70)
    print("APPROACH COMPARISON")
    print("=" * 70)
    
    approaches = [
        {
            "name": "Original (pdf_writer_improved.py)",
            "speed": "⭐ Slow (10-20 min)",
            "quality": "❌ Doesn't translate",
            "layout": "⭐⭐⭐ Good",
            "use_case": "❌ Don't use (broken)"
        },
        {
            "name": "Optimized (pdf_writer_fixed.py)",
            "speed": "⭐⭐⭐ Fast (3-5 min)",
            "quality": "✅ Actually translates",
            "layout": "⭐⭐⭐⭐ Very Good",
            "use_case": "✅ Best for most PDFs"
        },
        {
            "name": "Overlay (pdf_simple_overlay.py)",
            "speed": "⭐⭐⭐⭐ Very Fast (1-2 min)",
            "quality": "✅ Translates",
            "layout": "⭐⭐⭐⭐⭐ Perfect",
            "use_case": "✅ Best for scanned/image PDFs"
        },
        {
            "name": "Side-by-side (pdf_simple_overlay.py)",
            "speed": "⭐⭐⭐ Fast (3-4 min)",
            "quality": "✅ Translates",
            "layout": "⭐⭐⭐⭐⭐ Perfect (both shown)",
            "use_case": "✅ Best for comparison/learning"
        }
    ]
    
    for approach in approaches:
        print(f"\n{approach['name']}")
        print(f"  Speed:    {approach['speed']}")
        print(f"  Quality:  {approach['quality']}")
        print(f"  Layout:   {approach['layout']}")
        print(f"  Use Case: {approach['use_case']}")
        print("-" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python choose_approach.py <pdf_file>")
        print("\nOr run without arguments to see comparison table:")
        compare_approaches()
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_pdf(pdf_path)
    
    print("\n\n")
    compare_approaches()