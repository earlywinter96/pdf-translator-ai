"""
PDF Reader Service with OCR Support
----------------------------------
- Extracts text from text-based PDFs
- Automatically falls back to OCR for scanned PDFs
- Supports Gujarati, Marathi, Hindi
"""

from typing import List
import pdfplumber
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFReadError(Exception):
    pass


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def _ocr_page(image: Image.Image, ocr_lang: str, page_num: int) -> str:
    """Perform OCR on a single page image with timeout"""
    try:
        logger.info(f"Starting OCR on page {page_num} with language: {ocr_lang}")
        
        # Add timeout to prevent hanging (30 seconds per page)
        with timeout(30):
            text = pytesseract.image_to_string(
                image,
                lang=ocr_lang,
                config="--psm 6"
            )
        
        logger.info(f"OCR completed for page {page_num}, extracted {len(text)} characters")
        return text.strip()
        
    except TimeoutError as e:
        logger.error(f"OCR timeout on page {page_num}: {e}")
        return f"[OCR TIMEOUT - Page {page_num}]"
        
    except Exception as e:
        logger.error(f"OCR failed on page {page_num}: {e}")
        return f"[OCR ERROR - Page {page_num}]"


def extract_text_from_pdf(pdf_path: str, ocr_lang: str) -> List[str]:
    """
    Extract text from PDF pages.
    Uses OCR ONLY when extracted text is insufficient.
    """

    MIN_TEXT_LENGTH = 60  # Critical threshold
    pages_text: List[str] = []

    if not os.path.exists(pdf_path):
        raise PDFReadError("PDF file does not exist")

    temp_dir = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF opened successfully. Pages: {total_pages}")
            
            # Limit pages to prevent memory issues
            if total_pages > 400:
                raise PDFReadError(f"PDF has {total_pages} pages. Maximum allowed is 400.")

            for page_number, page in enumerate(pdf.pages, start=1):
                text = ""

                try:
                    # 1️⃣ Try normal text extraction first
                    extracted = page.extract_text() or ""
                    text = extracted.strip()
                    logger.info(f"Page {page_number}: Extracted {len(text)} chars via pdfplumber")

                except Exception as e:
                    logger.warning(f"Text extraction failed on page {page_number}: {e}")

                # 2️⃣ OCR fallback ONLY if text is insufficient
                if len(text) < MIN_TEXT_LENGTH:
                    logger.info(f"Using OCR for page {page_number} (extracted text too short: {len(text)} chars)")

                    try:
                        # Create temp directory only when needed
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                            logger.info(f"Created temp directory: {temp_dir}")
                        
                        # Convert ONLY the current page to reduce memory usage
                        with timeout(60):  # 60 second timeout for image conversion
                            images = convert_from_path(
                                pdf_path,
                                first_page=page_number,
                                last_page=page_number,
                                dpi=200,  # Reduced from 250 to save memory
                                output_folder=temp_dir,
                                fmt='jpeg',  # JPEG uses less memory than PNG
                                thread_count=1  # Limit threads to reduce memory
                            )

                        if images:
                            text = _ocr_page(images[0], ocr_lang, page_number).strip()
                            logger.info(f"OCR extracted {len(text)} chars from page {page_number}")
                            
                            # Clean up image immediately
                            images[0].close()
                            del images
                        else:
                            logger.warning(f"No images generated for page {page_number}")
                            
                    except TimeoutError:
                        logger.error(f"Image conversion timeout on page {page_number}")
                        text = f"[PAGE CONVERSION TIMEOUT - Page {page_number}]"
                        
                    except Exception as e:
                        logger.error(f"OCR process failed for page {page_number}: {e}")
                        text = f"[OCR FAILED - Page {page_number}]"

                # 3️⃣ Normalize text
                if text:
                    cleaned = (
                        text.replace("\u00a0", " ")
                            .replace("\t", " ")
                            .strip()
                    )
                    pages_text.append(cleaned)
                else:
                    logger.warning(f"No usable text on page {page_number}")
                    pages_text.append(f"[EMPTY PAGE {page_number}]")

    except Exception as e:
        logger.exception("Failed to read PDF")
        raise PDFReadError(f"PDF reading failed: {str(e)}")
    
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

    if not any(pages_text):
        raise PDFReadError("No extractable text found (OCR also failed)")

    logger.info("PDF text extraction (hybrid OCR) completed successfully")
    return pages_text