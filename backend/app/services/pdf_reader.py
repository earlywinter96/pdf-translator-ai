"""
PDF Text Extraction Service - IMPROVED VERSION
===============================================
Robust PDF text extraction with OCR fallback, blank page detection,
and proper language validation
"""

import os
import logging
from typing import List, Optional, Tuple
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from langdetect import detect, LangDetectException
import re

logger = logging.getLogger(__name__)

# ============================================================================
# LANGUAGE MAPPING
# ============================================================================

# Map common language codes to Tesseract language codes
TESSERACT_LANG_MAP = {
    "gujarati": "guj",
    "hindi": "hin", 
    "marathi": "mar",
    "tamil": "tam",
    "telugu": "tel",
    "kannada": "kan",
    "malayalam": "mal",
    "bengali": "ben",
    "punjabi": "pan",
    "english": "eng",
    "en": "eng",
    "gu": "guj",
    "hi": "hin",
    "mr": "mar",
    "ta": "tam",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "bn": "ben",
    "pa": "pan"
}

# Reverse mapping for display names
LANG_DISPLAY_NAMES = {
    "eng": "English",
    "guj": "Gujarati", 
    "hin": "Hindi",
    "mar": "Marathi",
    "tam": "Tamil",
    "tel": "Telugu",
    "kan": "Kannada",
    "mal": "Malayalam",
    "ben": "Bengali",
    "pan": "Punjabi"
}

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_CHARS_FOR_VALID_PAGE = 50  # Minimum characters to consider a page non-blank
MIN_CHARS_FOR_OCR_TRIGGER = 100  # If direct extraction gives less, try OCR
OCR_CONFIDENCE_THRESHOLD = 60  # Minimum OCR confidence (0-100)


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

def detect_text_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of text
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (language_code, confidence)
    """
    if not text or len(text.strip()) < 20:
        return "unknown", 0.0
    
    try:
        # Use langdetect
        detected = detect(text)
        
        # Count script characters to boost confidence
        gujarati_chars = len(re.findall(r'[\u0A80-\u0AFF]', text))
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = len(text)
        
        # If >70% non-Latin, boost Indian language detection
        if total_chars > 0:
            if gujarati_chars / total_chars > 0.7:
                return "gu", 0.95
            elif devanagari_chars / total_chars > 0.7:
                return "hi", 0.90  # Could be Hindi/Marathi
            elif latin_chars / total_chars > 0.7:
                return "en", 0.95
        
        # Use langdetect result with medium confidence
        return detected, 0.70
        
    except LangDetectException:
        logger.warning("Language detection failed, defaulting to unknown")
        return "unknown", 0.0


def detect_pdf_language(pdf_path: str, sample_pages: int = 3) -> Tuple[str, float]:
    """
    Detect the primary language of a PDF by sampling pages
    
    Args:
        pdf_path: Path to PDF file
        sample_pages: Number of pages to sample
        
    Returns:
        Tuple of (language_code, confidence)
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            # Sample pages evenly distributed
            pages_to_check = min(sample_pages, total_pages)
            step = max(1, total_pages // pages_to_check)
            
            all_text = ""
            for i in range(0, total_pages, step):
                if len(all_text) > 1000:  # Enough sample
                    break
                page = pdf_reader.pages[i]
                all_text += page.extract_text() or ""
            
            # If no text extracted, try OCR on first page
            if not all_text.strip():
                logger.warning("No text extracted for language detection, trying OCR...")
                try:
                    # Use OCR with English first to detect language
                    ocr_text, _ = extract_page_with_ocr(pdf_path, 0, "eng")
                    if ocr_text.strip():
                        all_text = ocr_text
                        logger.info(f"   OCR extracted {len(ocr_text)} chars for language detection")
                    else:
                        logger.warning("OCR also failed to extract text")
                        return "unknown", 0.0
                except Exception as e:
                    logger.error(f"OCR language detection failed: {e}")
                    return "unknown", 0.0
            
            if not all_text.strip():
                logger.warning("No text available for language detection")
                return "unknown", 0.0
            
            lang, confidence = detect_text_language(all_text)
            
            logger.info(f"📊 Language Detection Results:")
            logger.info(f"   Detected: {lang} (confidence: {confidence*100:.0f}%)")
            logger.info(f"   Sample size: {len(all_text)} chars from {pages_to_check} pages")
            
            return lang, confidence
            
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return "unknown", 0.0


# ============================================================================
# TEXT EXTRACTION
# ============================================================================

def is_blank_page(text: str) -> bool:
    """
    Check if a page is effectively blank
    
    Args:
        text: Extracted text from page
        
    Returns:
        True if page is blank/minimal content
    """
    if not text:
        return True
    
    # Remove whitespace and common artifacts
    cleaned = text.strip()
    cleaned = re.sub(r'\s+', '', cleaned)
    
    # Check if meaningful content exists
    return len(cleaned) < MIN_CHARS_FOR_VALID_PAGE


def extract_page_with_ocr(pdf_path: str, page_num: int, ocr_language: str) -> Tuple[str, float]:
    """
    Extract text from a page using OCR
    
    Args:
        pdf_path: Path to PDF
        page_num: Page number (0-indexed)
        ocr_language: Tesseract language code
        
    Returns:
        Tuple of (extracted_text, confidence)
    """
    try:
        # Convert page to image
        images = convert_from_path(
            pdf_path,
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=300
        )
        
        if not images:
            return "", 0.0
        
        # OCR with confidence data
        ocr_data = pytesseract.image_to_data(
            images[0],
            lang=ocr_language,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate average confidence
        text_parts = []
        confidences = []
        
        for i, word in enumerate(ocr_data['text']):
            if word.strip():
                text_parts.append(word)
                conf = int(ocr_data['conf'][i])
                if conf > 0:  # -1 means no confidence data
                    confidences.append(conf)
        
        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return text, avg_confidence
        
    except Exception as e:
        logger.error(f"OCR failed for page {page_num + 1}: {e}")
        return "", 0.0


def extract_pdf_text_robust(
    pdf_path: str,
    ocr_language: str = "eng",
    validate_language: Optional[str] = None
) -> Tuple[List[str], dict]:
    """
    Extract text from PDF with OCR fallback and validation
    
    Args:
        pdf_path: Path to PDF file
        ocr_language: Language for OCR (user-selected)
        validate_language: Expected language code for validation
        
    Returns:
        Tuple of (page_texts, metadata_dict)
    """
    # Map to Tesseract language code
    tesseract_lang = TESSERACT_LANG_MAP.get(ocr_language.lower(), "eng")
    
    logger.info(f"📖 Starting PDF extraction: {os.path.basename(pdf_path)}")
    logger.info(f"   OCR Language: {ocr_language} → {tesseract_lang}")
    
    # Detect actual PDF language
    detected_lang, detection_confidence = detect_pdf_language(pdf_path)
    
    # Validate if requested
    language_warning = None
    if validate_language:
        expected_codes = [validate_language, validate_language[:2]]
        if detected_lang not in expected_codes and detected_lang != "unknown":
            language_warning = {
                "expected": validate_language,
                "detected": detected_lang,
                "confidence": detection_confidence,
                "message": f"⚠️ PDF appears to be in {detected_lang}, but you selected {validate_language}"
            }
            logger.warning(language_warning["message"])
    
    # Open PDF
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"📄 PDF Info:")
            logger.info(f"   Total pages: {total_pages}")
            logger.info(f"   Tesseract: {'✅ Available' if pytesseract else '❌ Not available'}")
            
            page_texts = []
            stats = {
                "total_pages": total_pages,
                "blank_pages": 0,
                "direct_extraction": 0,
                "ocr_pages": 0,
                "failed_pages": 0,
                "total_chars": 0,
                "language_warning": language_warning
            }
            
            logger.info(f"📖 Extracting text from {total_pages} pages...")
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                
                # Try direct extraction first
                text = page.extract_text() or ""
                extraction_method = "direct"
                ocr_confidence = 100.0
                
                # If direct extraction gives minimal text, try OCR
                # Note: For scanned PDFs, direct extraction often returns empty or near-empty strings
                if len(text.strip()) < MIN_CHARS_FOR_OCR_TRIGGER:
                    logger.info(f"   Page {page_num + 1}: Direct extraction minimal ({len(text)} chars), trying OCR...")
                    ocr_text, ocr_confidence = extract_page_with_ocr(pdf_path, page_num, tesseract_lang)
                    
                    if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        extraction_method = "ocr"
                        stats["ocr_pages"] += 1
                        logger.info(f"   Page {page_num + 1}: {len(text)} chars (OCR, confidence: {ocr_confidence:.1f}%)")
                    elif not ocr_text.strip():
                        # Both direct and OCR failed - truly blank page
                        logger.info(f"   Page {page_num + 1}: BLANK (both direct and OCR failed)")
                        page_texts.append("")
                        stats["blank_pages"] += 1
                        continue
                    else:
                        # Direct extraction was better than OCR
                        stats["direct_extraction"] += 1
                        logger.info(f"   Page {page_num + 1}: {len(text)} chars (direct extraction)")
                else:
                    # Direct extraction gave good results
                    stats["direct_extraction"] += 1
                    logger.info(f"   Page {page_num + 1}: {len(text)} chars (direct extraction)")
                
                # Final blank page check after both attempts
                if is_blank_page(text):
                    logger.info(f"   Page {page_num + 1}: BLANK after extraction attempts")
                    page_texts.append("")
                    stats["blank_pages"] += 1
                    continue
                
                # Warn about low OCR confidence
                if extraction_method == "ocr" and ocr_confidence < OCR_CONFIDENCE_THRESHOLD:
                    logger.warning(f"   ⚠️ Low OCR confidence ({ocr_confidence:.1f}%) - results may be inaccurate")
                
                page_texts.append(text)
                stats["total_chars"] += len(text)
            
            logger.info("✅ Extraction complete:")
            logger.info(f"   Total chars: {stats['total_chars']:,}")
            logger.info(f"   Direct extraction: {stats['direct_extraction']}/{total_pages} pages")
            logger.info(f"   OCR used: {stats['ocr_pages']}/{total_pages} pages")
            logger.info(f"   Blank pages: {stats['blank_pages']}/{total_pages} pages")
            
            return page_texts, stats
            
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {e}", exc_info=True)
        raise


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_language_match(
    expected_lang: str,
    detected_lang: str,
    confidence: float
) -> dict:
    """
    Validate if detected language matches expected
    
    Args:
        expected_lang: User-selected language
        detected_lang: Auto-detected language
        confidence: Detection confidence
        
    Returns:
        Validation result dictionary
    """
    # Normalize codes
    expected_normalized = expected_lang.lower()[:2]
    detected_normalized = detected_lang.lower()[:2]
    
    match = expected_normalized == detected_normalized
    
    return {
        "match": match,
        "expected": expected_lang,
        "detected": detected_lang,
        "confidence": confidence,
        "should_warn": not match and confidence > 0.7,
        "message": (
            f"✅ Language match confirmed: {expected_lang}"
            if match
            else f"⚠️ Language mismatch: Expected {expected_lang}, detected {detected_lang}"
        )
    }


def get_non_blank_pages(page_texts: List[str]) -> List[Tuple[int, str]]:
    """
    Get list of non-blank pages with their indices
    
    Args:
        page_texts: List of page texts
        
    Returns:
        List of (page_index, text) tuples for non-blank pages
    """
    return [
        (i, text)
        for i, text in enumerate(page_texts)
        if not is_blank_page(text)
    ]