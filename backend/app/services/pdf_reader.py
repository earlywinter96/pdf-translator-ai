"""
PDF Reader Service with OCR Support - Fixed for Text Repetition
----------------------------------------------------------------
FIXES:
- Proper image preprocessing to avoid OCR repetition
- Better PSM mode selection
- Text deduplication logic
- Memory-efficient processing
"""

from typing import List
import pdfplumber
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import os
import tempfile
import gc
import subprocess
import time
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFReadError(Exception):
    pass


class TimeoutError(Exception):
    pass


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy and prevent repetition
    """
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Denoise - this is KEY to preventing repeated text
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Sharpen slightly
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        return image


def deduplicate_text(text: str) -> str:
    """
    Remove repeated lines/patterns from OCR output
    This is common when Tesseract processes images with artifacts
    """
    if not text:
        return text
    
    lines = text.split('\n')
    seen_lines = set()
    unique_lines = []
    
    for line in lines:
        # Clean the line
        cleaned = line.strip()
        
        # Skip empty lines but preserve spacing
        if not cleaned:
            unique_lines.append('')
            continue
        
        # Check for exact duplicates in a sliding window (last 5 lines)
        recent_window = unique_lines[-5:] if len(unique_lines) >= 5 else unique_lines
        if cleaned not in recent_window:
            unique_lines.append(line)
        else:
            logger.debug(f"Removed duplicate line: {cleaned[:50]}...")
    
    return '\n'.join(unique_lines)


def remove_repeated_patterns(text: str) -> str:
    """
    Remove patterns that repeat consecutively (common OCR artifact)
    Example: "hello hello" -> "hello"
    """
    # Pattern: word/phrase repeated 2+ times consecutively
    pattern = r'\b(\w+(?:\s+\w+){0,3})\s+\1\b'
    
    cleaned = text
    for _ in range(3):  # Multiple passes to catch nested repetitions
        before = cleaned
        cleaned = re.sub(pattern, r'\1', cleaned, flags=re.IGNORECASE)
        if cleaned == before:
            break
    
    return cleaned


def _ocr_page_with_subprocess(image_path: str, ocr_lang: str, page_num: int, timeout: int = 45) -> str:
    """
    Use subprocess for OCR with HARD timeout enforcement.
    FIXED: Better PSM mode and config for Indian languages
    """
    try:
        logger.info(f"Starting OCR on page {page_num} (timeout: {timeout}s)")
        
        # CRITICAL FIX: Use PSM 3 (automatic page segmentation) instead of PSM 6
        # PSM 3 is better for documents with mixed layouts
        # PSM 6 assumes uniform block of text (can cause repetition)
        cmd = [
            'tesseract',
            image_path,
            'stdout',
            '-l', ocr_lang,
            '--psm', '3',  # Changed from 6 to 3
            '--oem', '1',
            # Additional configs to improve accuracy
            '-c', 'tessedit_char_whitelist= ',  # Allow all chars
            '-c', 'preserve_interword_spaces=1'
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                logger.warning(f"Tesseract warning on page {page_num}: {result.stderr[:200]}")
            
            raw_text = result.stdout.strip()
            
            # CRITICAL: Apply deduplication
            cleaned_text = deduplicate_text(raw_text)
            cleaned_text = remove_repeated_patterns(cleaned_text)
            
            logger.info(f"OCR complete for page {page_num} in {elapsed:.1f}s: {len(cleaned_text)} chars (deduplicated from {len(raw_text)})")
            return cleaned_text
            
        except subprocess.TimeoutExpired:
            logger.error(f"OCR TIMEOUT on page {page_num} after {timeout}s")
            return f"[OCR TIMEOUT - Page {page_num}]"
        
    except Exception as e:
        logger.error(f"OCR subprocess failed on page {page_num}: {e}")
        return f"[OCR ERROR - Page {page_num}]"


def extract_text_from_pdf(pdf_path: str, ocr_lang: str) -> List[str]:
    """
    Extract text from PDF with ultra-robust OCR fallback.
    FIXED: Better image preprocessing and deduplication
    """
    MIN_TEXT_LENGTH = 60
    MAX_PAGES_FREE_TIER = 50
    pages_text: List[str] = []
    temp_dir = None
    
    if not os.path.exists(pdf_path):
        raise PDFReadError("PDF file does not exist")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"📄 PDF opened: {total_pages} pages")
            
            if total_pages > MAX_PAGES_FREE_TIER:
                raise PDFReadError(
                    f"PDF has {total_pages} pages. Maximum {MAX_PAGES_FREE_TIER} pages "
                    f"allowed on free tier. Please split your PDF or upgrade."
                )
            
            for page_number, page in enumerate(pdf.pages, start=1):
                logger.info(f"📖 Processing page {page_number}/{total_pages}")
                text = ""
                
                # Step 1: Try text extraction
                try:
                    extracted = page.extract_text() or ""
                    text = extracted.strip()
                    
                    # Apply deduplication even to extracted text
                    text = deduplicate_text(text)
                    text = remove_repeated_patterns(text)
                    
                    logger.info(f"   ✓ Text extraction: {len(text)} chars")
                except Exception as e:
                    logger.warning(f"   ✗ Text extraction failed: {e}")
                
                # Step 2: OCR fallback if needed
                if len(text) < MIN_TEXT_LENGTH:
                    logger.info(f"   → OCR needed (text too short: {len(text)} chars)")
                    
                    temp_image_path = None
                    
                    try:
                        # Create temp dir once
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                            logger.info(f"📁 Created temp dir: {temp_dir}")
                        
                        # Convert single page to image
                        logger.info(f"   Converting page {page_number} to image...")
                        
                        try:
                            # FIXED: Lower DPI and better format for OCR
                            images = convert_from_path(
                                pdf_path,
                                first_page=page_number,
                                last_page=page_number,
                                dpi=200,  # Increased from 150 for better OCR
                                output_folder=temp_dir,
                                fmt='png',  # Changed from jpeg - better for OCR
                                thread_count=1,
                                grayscale=False  # Keep color for preprocessing
                            )
                            
                            if not images:
                                raise Exception("No images generated")
                            
                            image = images[0]
                            
                            # CRITICAL: Preprocess image before OCR
                            image = preprocess_image_for_ocr(image)
                            
                            # Resize if too large (memory management)
                            max_dimension = 2500  # Increased slightly for better quality
                            if max(image.size) > max_dimension:
                                ratio = max_dimension / max(image.size)
                                new_size = tuple(int(dim * ratio) for dim in image.size)
                                image = image.resize(new_size, Image.LANCZOS)
                                logger.info(f"   Resized to {new_size}")
                            
                            # Save to temp file for subprocess
                            temp_image_path = os.path.join(temp_dir, f"page_{page_number}.png")
                            image.save(temp_image_path, 'PNG', optimize=True)
                            
                            # Close image immediately
                            image.close()
                            del images
                            gc.collect()
                            
                            logger.info(f"   ✓ Image saved: {temp_image_path}")
                            
                        except Exception as e:
                            logger.error(f"   ✗ Image conversion failed: {e}")
                            text = f"[IMAGE CONVERSION FAILED - Page {page_number}]"
                            continue
                        
                        # Perform OCR via subprocess with deduplication
                        if temp_image_path and os.path.exists(temp_image_path):
                            text = _ocr_page_with_subprocess(
                                temp_image_path, 
                                ocr_lang, 
                                page_number,
                                timeout=45
                            )
                        
                    except Exception as e:
                        logger.error(f"   ✗ OCR process failed: {e}")
                        text = f"[OCR FAILED - Page {page_number}]"
                    
                    finally:
                        # Clean up temp image
                        if temp_image_path and os.path.exists(temp_image_path):
                            try:
                                os.remove(temp_image_path)
                            except:
                                pass
                        gc.collect()
                
                # Step 3: Clean and store text
                if text:
                    # Final cleanup
                    cleaned = text.replace("\u00a0", " ").replace("\t", " ").strip()
                    # One more deduplication pass
                    cleaned = deduplicate_text(cleaned)
                    cleaned = remove_repeated_patterns(cleaned)
                    
                    pages_text.append(cleaned)
                    logger.info(f"   ✓ Page {page_number} complete: {len(cleaned)} chars")
                else:
                    logger.warning(f"   ⚠ No text on page {page_number}")
                    pages_text.append(f"[EMPTY PAGE {page_number}]")
                
                # Force cleanup after each page
                gc.collect()
    
    except Exception as e:
        logger.exception("❌ PDF reading failed")
        raise PDFReadError(f"PDF reading failed: {str(e)}")
    
    finally:
        # Final cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"🗑️ Cleaned up temp dir")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
        gc.collect()
    
    if not any(pages_text):
        raise PDFReadError("No extractable text found in PDF")
    
    logger.info(f"✅ Extraction complete: {len(pages_text)} pages processed")
    return pages_text