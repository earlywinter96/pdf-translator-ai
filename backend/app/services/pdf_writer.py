"""
PDF Writer Service - IMPROVED VERSION
======================================
Creates translated PDFs with proper formatting and blank page handling
"""

import os
import logging
from html import escape
from typing import List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Page size
DEFAULT_PAGE_SIZE = A4

# Margins
MARGIN_LEFT = 0.75 * inch
MARGIN_RIGHT = 0.75 * inch
MARGIN_TOP = 0.75 * inch
MARGIN_BOTTOM = 0.75 * inch

# Fonts
DEFAULT_FONT_SIZE = 11
LINE_SPACING = 1.4

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_FILES = {
    "NotoSans": "NotoSans-Regular.ttf",
    "NotoSansDevanagari": "NotoSansDevanagari-Regular.ttf",
    "NotoSansGujarati": "NotoSansGujarati-Regular.ttf",
}


# ============================================================================
# FONT REGISTRATION
# ============================================================================

def register_fonts() -> None:
    """
    Register fonts for different languages
    
    Bundled Noto fonts include the glyphs required for Hindi, Marathi, and
    Gujarati. Built-in ReportLab fonts such as Helvetica render those glyphs
    as black squares.
    """
    try:
        for font_name, filename in FONT_FILES.items():
            if font_name in pdfmetrics.getRegisteredFontNames():
                continue
            font_path = os.path.join(FONTS_DIR, filename)
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Required font is missing: {font_path}")
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            logger.info("Registered PDF font: %s", font_name)
    except Exception as e:
        logger.warning(f"Font registration warning: {e}")


# ============================================================================
# LANGUAGE-SPECIFIC SETTINGS
# ============================================================================

def get_language_config(language: str) -> dict:
    """
    Get language-specific configuration
    
    Args:
        language: Target language code
        
    Returns:
        Configuration dictionary
    """
    configs = {
        "english": {
            "font": "Helvetica",
            "font_size": 11,
            "alignment": TA_LEFT,
            "direction": "ltr"
        },
        "hindi": {
            "font": "NotoSansDevanagari",
            "font_size": 12,
            "alignment": TA_LEFT,
            "direction": "ltr"
        },
        "gujarati": {
            "font": "NotoSansGujarati",
            "font_size": 12,
            "alignment": TA_LEFT,
            "direction": "ltr"
        },
        "marathi": {
            "font": "NotoSansDevanagari",
            "font_size": 12,
            "alignment": TA_LEFT,
            "direction": "ltr"
        }
    }
    
    # Default config
    default = {
        "font": "Helvetica",
        "font_size": 11,
        "alignment": TA_LEFT,
        "direction": "ltr"
    }
    
    return configs.get(language.lower(), default)


# ============================================================================
# PDF CREATION
# ============================================================================

def clean_text_for_pdf(text: str) -> str:
    """
    Clean text for PDF rendering
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text safe for PDF
    """
    if not text:
        return ""
    
    # Replace problematic characters
    text = text.replace('\x00', '')  # Remove null bytes
    text = text.replace('\r\n', '\n')  # Normalize line breaks
    text = text.replace('\r', '\n')
    
    # Remove excessive whitespace but preserve paragraphs
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:  # Non-empty line
            cleaned_lines.append(line)
        elif cleaned_lines:  # Empty line (paragraph break)
            cleaned_lines.append('')
    
    return '\n'.join(cleaned_lines)


def create_translated_pdf(
    page_texts: List[str],
    output_path: str,
    target_language: str = "english",
    title: Optional[str] = None
):
    """
    Create a PDF from translated pages
    
    Args:
        page_texts: List of translated page texts
        output_path: Path to save PDF
        target_language: Target language for formatting
        title: Optional document title
    """
    logger.info(f"📝 Creating translated PDF: {output_path}")
    logger.info(f"   Pages: {len(page_texts)}")
    logger.info(f"   Language: {target_language}")
    
    # Register fonts
    register_fonts()
    
    # Get language config
    lang_config = get_language_config(target_language)
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=DEFAULT_PAGE_SIZE,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM
    )
    
    # Build styles
    styles = getSampleStyleSheet()
    
    # Create custom paragraph style
    custom_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=lang_config['font'],
        fontSize=lang_config['font_size'],
        leading=lang_config['font_size'] * LINE_SPACING,
        alignment=lang_config['alignment'],
        spaceAfter=12,
        wordWrap='LTR' if lang_config['direction'] == 'ltr' else 'RTL'
    )
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=lang_config['font'],
        fontSize=lang_config['font_size'] + 4,
        alignment=TA_LEFT,
        spaceAfter=20
    )
    
    # Build story (document content)
    story = []
    
    # Add title if provided
    if title:
        story.append(Paragraph(clean_text_for_pdf(title), title_style))
        story.append(Spacer(1, 0.3 * inch))
    
    # Process each page
    non_blank_count = 0
    blank_count = 0
    
    for page_num, text in enumerate(page_texts, 1):
        # Clean text
        cleaned_text = clean_text_for_pdf(text)
        
        # Skip blank pages
        if not cleaned_text or len(cleaned_text.strip()) < 10:
            logger.info(f"   Page {page_num}: Skipped (blank)")
            blank_count += 1
            # Still add page break to maintain page numbering
            if page_num < len(page_texts):  # Don't add break after last page
                story.append(PageBreak())
            continue
        
        non_blank_count += 1
        logger.info(f"   Page {page_num}: Added ({len(cleaned_text)} chars)")
        
        # Split into paragraphs
        paragraphs = cleaned_text.split('\n')
        
        for para_text in paragraphs:
            para_text = para_text.strip()
            if para_text:
                try:
                    # Create paragraph
                    # Paragraph uses an XML-like mini-markup language, so
                    # escape extracted document text before rendering it.
                    para = Paragraph(escape(para_text), custom_style)
                    story.append(para)
                except Exception as e:
                    # If paragraph creation fails, log and skip
                    logger.warning(f"   Failed to add paragraph: {e}")
                    logger.debug(f"   Problematic text: {para_text[:100]}...")
                    continue
            else:
                # Empty line = paragraph spacing
                story.append(Spacer(1, 0.15 * inch))
        
        # Add page break between pages (except after last page)
        if page_num < len(page_texts):
            story.append(PageBreak())
    
    # Build PDF
    try:
        doc.build(story)
        
        file_size = os.path.getsize(output_path)
        logger.info(f"✅ PDF created successfully: {output_path}")
        logger.info(f"   Non-blank pages: {non_blank_count}")
        logger.info(f"   Blank pages: {blank_count}")
        logger.info(f"   File size: {file_size / 1024:.1f} KB")
        
    except Exception as e:
        logger.error(f"❌ PDF creation failed: {e}", exc_info=True)
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def estimate_page_count(text: str, chars_per_page: int = 2000) -> int:
    """
    Estimate number of PDF pages needed for text
    
    Args:
        text: Input text
        chars_per_page: Approximate characters per page
        
    Returns:
        Estimated page count
    """
    if not text:
        return 0
    
    char_count = len(text)
    return max(1, (char_count + chars_per_page - 1) // chars_per_page)


def validate_output_path(output_path: str) -> bool:
    """
    Validate output path is writable
    
    Args:
        output_path: Path to validate
        
    Returns:
        True if valid
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Output path validation failed: {e}")
        return False
