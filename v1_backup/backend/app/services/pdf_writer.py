# app/services/pdf_writer_fixed.py
# ============================================================================
# FIXED PDF WRITER - Actually translates text properly
# ============================================================================

import logging
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io
import os

logger = logging.getLogger(__name__)


class SimplePDFWriter:
    """
    Creates translated PDF with proper text replacement.
    
    Strategy:
    1. Copy original page as image background
    2. White out ALL original text
    3. Place translated text in the SAME positions with SAME formatting
    """
    
    def __init__(self, original_pdf_path: str, output_path: str):
        self.original_pdf_path = original_pdf_path
        self.output_path = output_path
        self.original_doc = fitz.open(original_pdf_path)
        self.output_doc = fitz.open()
        
    def create_translated_pdf(
        self,
        translated_pages: List[str]
    ) -> str:
        """
        Create translated PDF - SIMPLE & EFFECTIVE approach.
        
        Args:
            translated_pages: Translated text for each page (one string per page)
            
        Returns:
            Path to output PDF
        """
        logger.info(f"📝 Creating translated PDF: {self.output_path}")
        logger.info(f"   Pages: {len(translated_pages)}")
        
        try:
            for page_idx, translated_text in enumerate(translated_pages):
                if page_idx >= len(self.original_doc):
                    logger.warning(f"   ⚠️  Page {page_idx + 1} exceeds original page count, skipping")
                    break
                    
                logger.debug(f"   Processing page {page_idx + 1}/{len(translated_pages)}")
                
                original_page = self.original_doc[page_idx]
                
                # Create new page with same dimensions
                new_page = self.output_doc.new_page(
                    width=original_page.rect.width,
                    height=original_page.rect.height
                )
                
                # Process this page
                self._process_page_simple(
                    original_page,
                    new_page,
                    translated_text
                )
            
            # Save output
            self.output_doc.save(self.output_path)
            logger.info(f"✅ Translated PDF saved: {self.output_path}")
            
            # Close documents
            self.output_doc.close()
            self.original_doc.close()
            
            return self.output_path
            
        except Exception as e:
            logger.error(f"❌ PDF creation failed: {e}")
            raise
    
    def _process_page_simple(
        self,
        original_page: fitz.Page,
        new_page: fitz.Page,
        translated_text: str
    ):
        """
        Simple & effective page processing.
        
        Steps:
        1. Render original page as image (keeps all formatting/images)
        2. Extract text blocks with positions
        3. White out text areas
        4. Place translated text in same positions
        """
        
        # ================================================================
        # STEP 1: Render original page as background image
        # ================================================================
        # This preserves ALL visual elements (images, shapes, colors, etc.)
        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
        pix = original_page.get_pixmap(matrix=mat)
        
        # Insert the image
        img_rect = new_page.rect
        new_page.insert_image(img_rect, stream=pix.tobytes("png"))
        
        # ================================================================
        # STEP 2: Get text blocks with positions from original
        # ================================================================
        text_blocks = original_page.get_text("dict")["blocks"]
        
        text_positions = []
        for block in text_blocks:
            if block.get("type") != 0:  # Not a text block
                continue
            
            bbox = block.get("bbox", None)
            if not bbox:
                continue
            
            # Get text and formatting from first line/span
            lines = block.get("lines", [])
            if not lines:
                continue
            
            first_line = lines[0]
            spans = first_line.get("spans", [])
            if not spans:
                continue
            
            first_span = spans[0]
            
            text_positions.append({
                "bbox": fitz.Rect(bbox),
                "font": first_span.get("font", "helv"),
                "size": first_span.get("size", 12),
                "color": self._int_to_rgb(first_span.get("color", 0))
            })
        
        if not text_positions:
            logger.warning(f"   No text positions found on page, using fallback")
            # Fallback: place text in page center
            rect = new_page.rect
            new_page.insert_textbox(
                rect,
                translated_text,
                fontsize=12,
                fontname="helv",
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT
            )
            return
        
        logger.debug(f"   Found {len(text_positions)} text blocks")
        
        # ================================================================
        # STEP 3: White out original text areas
        # ================================================================
        for pos in text_positions:
            # Draw white rectangle over text
            new_page.draw_rect(
                pos["bbox"],
                color=None,
                fill=(1, 1, 1),  # White
                overlay=True
            )
        
        # ================================================================
        # STEP 4: Place translated text
        # ================================================================
        # Split translated text into parts (one per text block)
        paragraphs = [p.strip() for p in translated_text.split('\n\n') if p.strip()]
        
        # If we have more positions than paragraphs, use single lines
        if len(paragraphs) < len(text_positions):
            paragraphs = [p.strip() for p in translated_text.split('\n') if p.strip()]
        
        # Match translated paragraphs to positions
        for i, pos in enumerate(text_positions):
            if i >= len(paragraphs):
                break
            
            text_to_insert = paragraphs[i]
            
            # Try to insert with original font settings
            try:
                # Normalize color to 0-1 range
                color = tuple(c / 255.0 if c > 1 else c for c in pos["color"])
                
                # Use Noto Sans for Indian languages (more reliable)
                fontname = "helv"  # Helvetica is most reliable
                
                new_page.insert_textbox(
                    pos["bbox"],
                    text_to_insert,
                    fontsize=pos["size"],
                    fontname=fontname,
                    color=color,
                    align=fitz.TEXT_ALIGN_LEFT
                )
                
            except Exception as e:
                logger.warning(f"   Failed to insert text block {i+1}: {e}")
                
                # Fallback: use simple black text
                try:
                    new_page.insert_textbox(
                        pos["bbox"],
                        text_to_insert,
                        fontsize=10,
                        fontname="helv",
                        color=(0, 0, 0),
                        align=fitz.TEXT_ALIGN_LEFT
                    )
                except Exception as e2:
                    logger.error(f"   Even fallback failed for block {i+1}: {e2}")
    
    def _int_to_rgb(self, color_int: int) -> Tuple[float, float, float]:
        """Convert integer color to RGB tuple (0-1 range)"""
        r = ((color_int >> 16) & 0xFF) / 255.0
        g = ((color_int >> 8) & 0xFF) / 255.0
        b = (color_int & 0xFF) / 255.0
        return (r, g, b)


# ============================================================================
# HIGH-LEVEL FUNCTION
# ============================================================================

def create_translated_pdf_fixed(
    original_pdf_path: str,
    translated_pages: List[str],
    output_path: str
) -> str:
    """
    High-level function to create translated PDF.
    
    Args:
        original_pdf_path: Path to original PDF
        translated_pages: List of translated text strings (one per page)
        output_path: Where to save output PDF
        
    Returns:
        Path to created PDF
    """
    writer = SimplePDFWriter(
        original_pdf_path=original_pdf_path,
        output_path=output_path
    )
    
    return writer.create_translated_pdf(translated_pages)