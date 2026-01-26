"""
PDF Reader Service - Optimized for 512MB Free Tier
---------------------------------------------------
FIXES:
1. Increased OCR timeout (45s → 120s)
2. Aggressive memory cleanup
3. Sequential processing (no concurrent pages)
4. Smaller image sizes
5. Early failure detection
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
import psutil  # For memory monitoring

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFReadError(Exception):
    pass


def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Preprocess image - optimized for low memory"""
    try:
        # Convert to grayscale (saves memory)
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Denoise - prevents repeated text
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Sharpen
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        return image


def deduplicate_text(text: str) -> str:
    """Remove repeated lines from OCR output"""
    if not text:
        return text
    
    lines = text.split('\n')
    unique_lines = []
    recent_window = []
    
    for line in lines:
        cleaned = line.strip()
        
        if not cleaned:
            unique_lines.append('')
            continue
        
        # Check last 5 lines for duplicates
        if cleaned not in recent_window:
            unique_lines.append(line)
            recent_window.append(cleaned)
            if len(recent_window) > 5:
                recent_window.pop(0)
    
    return '\n'.join(unique_lines)


def remove_repeated_patterns(text: str) -> str:
    """Remove consecutive word/phrase repetitions"""
    pattern = r'\b(\w+(?:\s+\w+){0,3})\s+\1\b'
    
    cleaned = text
    for _ in range(3):
        before = cleaned
        cleaned = re.sub(pattern, r'\1', cleaned, flags=re.IGNORECASE)
        if cleaned == before:
            break
    
    return cleaned


def _ocr_page_with_subprocess(image_path: str, ocr_lang: str, page_num: int, timeout: int = 120) -> str:
    """
    OCR with subprocess - INCREASED TIMEOUT for free tier
    """
    try:
        mem_before = get_memory_usage()
        logger.info(f"🔍 Starting OCR on page {page_num} (timeout: {timeout}s, memory: {mem_before:.1f}MB)")
        
        # Use PSM 3 for better page segmentation
        cmd = [
            'tesseract',
            image_path,
            'stdout',
            '-l', ocr_lang,
            '--psm', '3',  # Automatic page segmentation
            '--oem', '1',
            '-c', 'preserve_interword_spaces=1'
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,  # Increased to 120s
                check=False
            )
            
            elapsed = time.time() - start_time
            mem_after = get_memory_usage()
            
            if result.returncode != 0:
                logger.warning(f"Tesseract warning: {result.stderr[:200]}")
            
            raw_text = result.stdout.strip()
            
            # Apply deduplication
            cleaned_text = deduplicate_text(raw_text)
            cleaned_text = remove_repeated_patterns(cleaned_text)
            
            logger.info(
                f"✅ OCR done for page {page_num}: {elapsed:.1f}s, "
                f"{len(cleaned_text)} chars (from {len(raw_text)}), "
                f"memory: {mem_after:.1f}MB"
            )
            
            return cleaned_text
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ OCR TIMEOUT on page {page_num} after {timeout}s")
            return f"[OCR TIMEOUT - Page {page_num}]\n\nThis page took too long to process. Try a higher quality scan or smaller PDF."
        
    except Exception as e:
        logger.error(f"❌ OCR failed on page {page_num}: {e}")
        return f"[OCR ERROR - Page {page_num}]\n\nError: {str(e)}"


def extract_text_from_pdf(pdf_path: str, ocr_lang: str) -> List[str]:
    """
    Extract text from PDF - OPTIMIZED FOR FREE TIER
    
    Changes:
    - Smaller images (DPI 150 instead of 200)
    - Aggressive memory cleanup
    - Lower page limit (20 pages for free tier)
    - Early failure detection
    """
    MIN_TEXT_LENGTH = 60
    MAX_PAGES_FREE_TIER = 20  # REDUCED from 50
    pages_text: List[str] = []
    temp_dir = None
    
    if not os.path.exists(pdf_path):
        raise PDFReadError("PDF file does not exist")
    
    logger.info(f"📊 Initial memory: {get_memory_usage():.1f}MB")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"📄 PDF opened: {total_pages} pages")
            
            if total_pages > MAX_PAGES_FREE_TIER:
                raise PDFReadError(
                    f"PDF has {total_pages} pages. Free tier limit is {MAX_PAGES_FREE_TIER} pages. "
                    f"Please split your PDF into smaller files."
                )
            
            for page_number, page in enumerate(pdf.pages, start=1):
                logger.info(f"📖 Processing page {page_number}/{total_pages}")
                text = ""
                
                # Check memory before processing
                mem_usage = get_memory_usage()
                if mem_usage > 400:  # If using >400MB, cleanup aggressively
                    logger.warning(f"⚠️ High memory usage: {mem_usage:.1f}MB - forcing cleanup")
                    gc.collect()
                
                # Step 1: Try text extraction
                try:
                    extracted = page.extract_text() or ""
                    text = extracted.strip()
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
                        
                        logger.info(f"   Converting page {page_number} to image...")
                        
                        try:
                            # REDUCED DPI for free tier (150 instead of 200)
                            images = convert_from_path(
                                pdf_path,
                                first_page=page_number,
                                last_page=page_number,
                                dpi=150,  # Lower DPI = less memory
                                output_folder=temp_dir,
                                fmt='png',
                                thread_count=1,
                                grayscale=False
                            )
                            
                            if not images:
                                raise Exception("No images generated")
                            
                            image = images[0]
                            
                            # Preprocess
                            image = preprocess_image_for_ocr(image)
                            
                            # Resize if too large (REDUCED max size)
                            max_dimension = 2000  # Reduced from 2500
                            if max(image.size) > max_dimension:
                                ratio = max_dimension / max(image.size)
                                new_size = tuple(int(dim * ratio) for dim in image.size)
                                image = image.resize(new_size, Image.LANCZOS)
                                logger.info(f"   Resized to {new_size}")
                            
                            # Save
                            temp_image_path = os.path.join(temp_dir, f"page_{page_number}.png")
                            image.save(temp_image_path, 'PNG', optimize=True)
                            
                            # Immediate cleanup
                            image.close()
                            del images
                            gc.collect()
                            
                            logger.info(f"   ✓ Image saved: {temp_image_path}")
                            
                        except Exception as e:
                            logger.error(f"   ✗ Image conversion failed: {e}")
                            text = f"[IMAGE CONVERSION FAILED - Page {page_number}]"
                            pages_text.append(text)
                            continue
                        
                        # OCR with increased timeout (120s)
                        if temp_image_path and os.path.exists(temp_image_path):
                            text = _ocr_page_with_subprocess(
                                temp_image_path, 
                                ocr_lang, 
                                page_number,
                                timeout=120  # Increased from 45s
                            )
                        
                    except Exception as e:
                        logger.error(f"   ✗ OCR process failed: {e}")
                        text = f"[OCR FAILED - Page {page_number}]"
                    
                    finally:
                        # Clean up temp image IMMEDIATELY
                        if temp_image_path and os.path.exists(temp_image_path):
                            try:
                                os.remove(temp_image_path)
                            except:
                                pass
                        gc.collect()
                
                # Step 3: Store text
                if text:
                    cleaned = text.replace("\u00a0", " ").replace("\t", " ").strip()
                    cleaned = deduplicate_text(cleaned)
                    cleaned = remove_repeated_patterns(cleaned)
                    pages_text.append(cleaned)
                    logger.info(f"   ✓ Page {page_number} complete: {len(cleaned)} chars")
                else:
                    logger.warning(f"   ⚠ No text on page {page_number}")
                    pages_text.append(f"[EMPTY PAGE {page_number}]")
                
                # Force cleanup after EACH page
                gc.collect()
                logger.info(f"   💾 Memory after page: {get_memory_usage():.1f}MB")
    
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
        logger.info(f"📊 Final memory: {get_memory_usage():.1f}MB")
    
    if not any(pages_text):
        raise PDFReadError("No extractable text found in PDF")
    
    logger.info(f"✅ Extraction complete: {len(pages_text)} pages processed")
    return pages_text