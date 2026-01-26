"""
PDF Reader Service with OCR Support - Optimized for Low Memory
--------------------------------------------------------------
- Reduced memory footprint for Render free tier (512MB)
- Better timeout handling
- Aggressive cleanup
"""

from typing import List
import pdfplumber
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile
import threading
import gc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFReadError(Exception):
    pass


class TimeoutError(Exception):
    pass


def timeout_handler(func, args=(), kwargs={}, timeout_duration=30):
    """Thread-based timeout that works in Docker"""
    result = [TimeoutError("Operation timed out")]
    
    def wrapper():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            result[0] = e
    
    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    thread.join(timeout_duration)
    
    if thread.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout_duration} seconds")
    
    if isinstance(result[0], Exception):
        raise result[0]
    
    return result[0]


def _ocr_page(image: Image.Image, ocr_lang: str, page_num: int) -> str:
    """Perform OCR on a single page with aggressive memory cleanup"""
    try:
        logger.info(f"Starting OCR on page {page_num} (lang: {ocr_lang})")
        
        # Resize image if too large (save memory)
        max_dimension = 2000
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.LANCZOS)
            logger.info(f"Resized image to {new_size} to save memory")
        
        # Perform OCR with timeout
        def ocr_task():
            return pytesseract.image_to_string(
                image,
                lang=ocr_lang,
                config="--psm 6 --oem 1"  # Use LSTM engine for better accuracy
            )
        
        text = timeout_handler(ocr_task, timeout_duration=45)
        
        logger.info(f"OCR complete for page {page_num}: {len(text)} chars")
        return text.strip()
        
    except TimeoutError as e:
        logger.error(f"OCR timeout on page {page_num}: {e}")
        return f"[OCR TIMEOUT - Page {page_num}]"
        
    except Exception as e:
        logger.error(f"OCR failed on page {page_num}: {e}")
        return f"[OCR ERROR - Page {page_num}: {str(e)}]"
    
    finally:
        # Force cleanup
        gc.collect()


def extract_text_from_pdf(pdf_path: str, ocr_lang: str) -> List[str]:
    """
    Extract text from PDF with memory-optimized OCR fallback
    """
    MIN_TEXT_LENGTH = 60
    MAX_PAGES_FREE_TIER = 50  # Reduced from 400 for free tier
    pages_text: List[str] = []

    if not os.path.exists(pdf_path):
        raise PDFReadError("PDF file does not exist")

    temp_dir = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF opened: {total_pages} pages")
            
            # Strict limit for free tier
            if total_pages > MAX_PAGES_FREE_TIER:
                raise PDFReadError(
                    f"PDF has {total_pages} pages. Maximum {MAX_PAGES_FREE_TIER} pages "
                    f"allowed on free tier. Please upgrade or split your PDF."
                )

            for page_number, page in enumerate(pdf.pages, start=1):
                logger.info(f"Processing page {page_number}/{total_pages}")
                text = ""

                try:
                    # Try text extraction first
                    extracted = page.extract_text() or ""
                    text = extracted.strip()
                    logger.info(f"Page {page_number}: {len(text)} chars extracted")

                except Exception as e:
                    logger.warning(f"Text extraction failed on page {page_number}: {e}")

                # OCR fallback if needed
                if len(text) < MIN_TEXT_LENGTH:
                    logger.info(f"Using OCR for page {page_number}")

                    try:
                        # Create temp dir only when needed
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                        
                        # Convert single page with reduced DPI
                        def convert_task():
                            return convert_from_path(
                                pdf_path,
                                first_page=page_number,
                                last_page=page_number,
                                dpi=150,  # Reduced from 200
                                output_folder=temp_dir,
                                fmt='jpeg',
                                thread_count=1,
                                grayscale=True  # Save memory
                            )
                        
                        images = timeout_handler(convert_task, timeout_duration=60)

                        if images:
                            text = _ocr_page(images[0], ocr_lang, page_number).strip()
                            
                            # Cleanup immediately
                            images[0].close()
                            del images
                            gc.collect()
                        else:
                            logger.warning(f"No images generated for page {page_number}")
                            
                    except TimeoutError:
                        logger.error(f"Conversion timeout on page {page_number}")
                        text = f"[PAGE CONVERSION TIMEOUT - Page {page_number}]"
                        
                    except Exception as e:
                        logger.error(f"OCR failed for page {page_number}: {e}")
                        text = f"[OCR FAILED - Page {page_number}]"

                # Add normalized text
                if text:
                    cleaned = (
                        text.replace("\u00a0", " ")
                            .replace("\t", " ")
                            .strip()
                    )
                    pages_text.append(cleaned)
                else:
                    logger.warning(f"No text on page {page_number}")
                    pages_text.append(f"[EMPTY PAGE {page_number}]")
                
                # Force garbage collection after each page
                gc.collect()

    except Exception as e:
        logger.exception("Failed to read PDF")
        raise PDFReadError(f"PDF reading failed: {str(e)}")
    
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp: {temp_dir}")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
        
        # Final garbage collection
        gc.collect()

    if not any(pages_text):
        raise PDFReadError("No extractable text found")

    logger.info(f"Extraction complete: {len(pages_text)} pages")
    return pages_text