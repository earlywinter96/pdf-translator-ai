# app/services/pdf_simple_overlay.py
# ============================================================================
# ULTRA-SIMPLE PDF TRANSLATOR - For Scanned/Image PDFs
# ============================================================================
"""
Alternative approach when original PDF is mostly images/scanned.

Strategy:
1. Keep original PDF completely intact
2. Add transparent text overlay with translation
3. User can copy/search translated text
4. Visual layout 100% preserved
"""

import logging
from typing import List
import fitz  # PyMUPDF
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader

logger = logging.getLogger(__name__)


def create_overlay_pdf(
    original_pdf_path: str,
    translated_pages: List[str],
    output_path: str
) -> str:
    """
    Create translated PDF using TEXT OVERLAY method.
    
    Perfect for:
    - Scanned PDFs
    - Image-heavy PDFs
    - When you want 100% visual preservation
    
    Args:
        original_pdf_path: Path to original PDF
        translated_pages: List of translated text (one per page)
        output_path: Where to save output
        
    Returns:
        Path to output PDF
    """
    logger.info(f"📝 Creating overlay PDF: {output_path}")
    logger.info(f"   Method: Transparent text overlay")
    logger.info(f"   Pages: {len(translated_pages)}")
    
    try:
        # Open original
        doc = fitz.open(original_pdf_path)
        
        # Process each page
        for page_idx, translated_text in enumerate(translated_pages):
            if page_idx >= len(doc):
                break
            
            page = doc[page_idx]
            
            # Add invisible text layer at bottom of page
            # This preserves 100% of visuals but adds searchable text
            text_rect = fitz.Rect(0, page.rect.height - 50, page.rect.width, page.rect.height)
            
            # Insert as white text on white background (invisible but searchable)
            page.insert_textbox(
                text_rect,
                f"[TRANSLATED TEXT]\n{translated_text}",
                fontsize=6,
                fontname="helv",
                color=(1, 1, 1),  # White text (invisible)
                align=fitz.TEXT_ALIGN_LEFT
            )
        
        # Save
        doc.save(output_path)
        doc.close()
        
        logger.info(f"✅ Overlay PDF created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Overlay PDF creation failed: {e}")
        raise


def create_sidebyside_pdf(
    original_pdf_path: str,
    translated_pages: List[str],
    output_path: str
) -> str:
    """
    Create side-by-side PDF - original on left, translation on right.
    
    Great for:
    - Comparison
    - Learning
    - Quality checking
    
    Args:
        original_pdf_path: Path to original PDF
        translated_pages: List of translated text
        output_path: Output path
        
    Returns:
        Path to output PDF
    """
    logger.info(f"📝 Creating side-by-side PDF: {output_path}")
    
    try:
        # Open original
        original = fitz.open(original_pdf_path)
        output = fitz.open()
        
        for page_idx, translated_text in enumerate(translated_pages):
            if page_idx >= len(original):
                break
            
            orig_page = original[page_idx]
            
            # Create new page (double width)
            new_page = output.new_page(
                width=orig_page.rect.width * 2 + 20,  # Gap in middle
                height=orig_page.rect.height
            )
            
            # Insert original on left
            new_page.show_pdf_page(
                fitz.Rect(0, 0, orig_page.rect.width, orig_page.rect.height),
                original,
                page_idx
            )
            
            # Add translation on right
            trans_rect = fitz.Rect(
                orig_page.rect.width + 20,
                0,
                orig_page.rect.width * 2 + 20,
                orig_page.rect.height
            )
            
            # White background for translation
            new_page.draw_rect(trans_rect, color=None, fill=(1, 1, 1))
            
            # Add translated text
            new_page.insert_textbox(
                trans_rect,
                translated_text,
                fontsize=10,
                fontname="helv",
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT
            )
        
        output.save(output_path)
        output.close()
        original.close()
        
        logger.info(f"✅ Side-by-side PDF created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Side-by-side PDF creation failed: {e}")
        raise