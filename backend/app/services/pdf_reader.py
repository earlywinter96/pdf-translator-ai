import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import time

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Environment-based configuration
OCR_TIMEOUT = int(os.getenv('TESSERACT_TIMEOUT', 180))
OCR_DPI = int(os.getenv('OCR_DPI', 150))
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 1600))

# OCR language mapping
LANGUAGE_MAP = {
    'gu': 'guj',  # Gujarati
    'mr': 'mar',  # Marathi
    'hi': 'hin',  # Hindi
    'en': 'eng',  # English
}


class PDFReader:
    """
    Thread-safe PDF reader with fast OCR support.
    Works with FastAPI background tasks and threading.
    """
    
    def __init__(self, pdf_path: str, language: str = 'en'):
        self.pdf_path = Path(pdf_path)
        self.language = language
        self.ocr_lang = LANGUAGE_MAP.get(language, 'eng')
        self.doc = None
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Initializing PDF reader for: {pdf_path}")
        logger.info(f"Language: {language} -> OCR: {self.ocr_lang}")
        logger.info(f"OCR Settings - DPI: {OCR_DPI}, Timeout: {OCR_TIMEOUT}s, Max Size: {MAX_IMAGE_SIZE}px")
    
    def open(self) -> int:
        """Open PDF and return page count."""
        try:
            self.doc = fitz.open(self.pdf_path)
            page_count = len(self.doc)
            logger.info(f"PDF opened: {page_count} pages")
            return page_count
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise
    
    def close(self):
        """Close PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None
            logger.info("PDF closed")
    
    def extract_text_from_page(self, page_num: int) -> str:
        """
        Extract text from a single page.
        First tries native text extraction, falls back to OCR if needed.
        """
        if not self.doc:
            raise RuntimeError("PDF not opened. Call open() first.")
        
        if page_num < 1 or page_num > len(self.doc):
            raise ValueError(f"Invalid page number: {page_num}")
        
        logger.info(f"📄 Processing page {page_num}/{len(self.doc)}")
        
        # Get page (0-indexed internally)
        page = self.doc[page_num - 1]
        
        # Try native text extraction first
        text = page.get_text().strip()
        logger.info(f"  Native extraction: {len(text)} chars")
        
        # If no text or very little text, use OCR
        if len(text) < 50:
            logger.info(f"  🔍 Using OCR (insufficient text)")
            text = self._ocr_page(page_num)
        
        return text
    
    def _ocr_page(self, page_num: int) -> str:
        """
        Perform FAST OCR on a page - THREAD SAFE (no signals).
        Uses pytesseract's built-in timeout mechanism.
        """
        try:
            # Step 1: Convert PDF to image
            logger.info(f"  ⏱️  Converting to image...")
            start_time = time.time()
            
            images = self._convert_page_to_image(page_num)
            
            conversion_time = time.time() - start_time
            logger.info(f"  ✅ Converted in {conversion_time:.1f}s")
            
            if not images:
                logger.error(f"  ❌ No images generated")
                return ""
            
            image = images[0]
            logger.info(f"  📐 Image size: {image.size}")
            
            # Step 2: Preprocess image
            image = self._fast_preprocess(image)
            
            # Step 3: OCR with pytesseract's built-in timeout
            logger.info(f"  🔤 Running OCR (timeout: {OCR_TIMEOUT}s)...")
            ocr_start = time.time()
            
            # Optimized config for speed
            custom_config = (
                f'--oem 1 '  # LSTM only (fastest)
                f'--psm 3 '  # Automatic page segmentation
                f'-l {self.ocr_lang} '
            )
            
            try:
                # Use pytesseract's built-in timeout (works in threads)
                text = pytesseract.image_to_string(
                    image,
                    config=custom_config,
                    timeout=OCR_TIMEOUT  # This works in background threads
                )
            except RuntimeError as e:
                if "timeout" in str(e).lower():
                    logger.error(f"  ❌ OCR timeout ({OCR_TIMEOUT}s)")
                    return ""
                logger.error(f"  ❌ OCR error: {e}")
                return ""
            except Exception as e:
                logger.error(f"  ❌ OCR error: {e}")
                return ""
            
            ocr_time = time.time() - ocr_start
            logger.info(f"  ✅ OCR completed in {ocr_time:.1f}s: {len(text)} chars")
            
            # Cleanup
            image.close()
            del images
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"  ❌ OCR failed: {e}")
            return ""
    
    def _convert_page_to_image(self, page_num: int):
        """Convert PDF page to image with optimizations."""
        try:
            return convert_from_path(
                str(self.pdf_path),
                dpi=OCR_DPI,
                first_page=page_num,
                last_page=page_num,
                fmt='jpeg',  # JPEG is faster than PNG
                thread_count=1,
                grayscale=True,
                size=(MAX_IMAGE_SIZE, None)
            )
        except Exception as e:
            logger.error(f"  ❌ Image conversion failed: {e}")
            return []
    
    def _fast_preprocess(self, image: Image.Image) -> Image.Image:
        """Fast image preprocessing for OCR."""
        try:
            # Ensure grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Aggressive resize if too large
            if image.width > MAX_IMAGE_SIZE or image.height > MAX_IMAGE_SIZE:
                ratio = min(MAX_IMAGE_SIZE / image.width, MAX_IMAGE_SIZE / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"  📏 Resized to: {image.size}")
            
            # Light contrast enhancement for better OCR
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            return image
        except Exception as e:
            logger.warning(f"  ⚠️ Preprocessing warning: {e}")
            return image
    
    def extract_all_text(self, progress_callback=None) -> List[Dict[str, any]]:
        """Extract text from all pages with progress reporting."""
        if not self.doc:
            raise RuntimeError("PDF not opened. Call open() first.")
        
        results = []
        total_pages = len(self.doc)
        
        logger.info(f"🚀 Starting extraction of {total_pages} pages")
        total_start = time.time()
        
        for page_num in range(1, total_pages + 1):
            try:
                text = self.extract_text_from_page(page_num)
                
                results.append({
                    'page': page_num,
                    'text': text,
                    'char_count': len(text)
                })
                
                if progress_callback:
                    progress_callback(page_num, total_pages, text)
                
            except Exception as e:
                logger.error(f"❌ Failed to extract page {page_num}: {e}")
                results.append({
                    'page': page_num,
                    'text': '',
                    'error': str(e)
                })
        
        total_time = time.time() - total_start
        total_chars = sum(r.get('char_count', 0) for r in results)
        logger.info(f"✅ Extraction complete: {total_pages} pages, {total_chars} chars in {total_time:.1f}s")
        
        if total_pages > 0:
            logger.info(f"⚡ Average: {total_time/total_pages:.1f}s per page")
        
        return results
    
    def get_page_count(self) -> int:
        """Get total number of pages."""
        if not self.doc:
            raise RuntimeError("PDF not opened. Call open() first.")
        return len(self.doc)
    
    def get_metadata(self) -> Dict[str, any]:
        """Get PDF metadata."""
        if not self.doc:
            raise RuntimeError("PDF not opened. Call open() first.")
        
        metadata = self.doc.metadata
        file_size = self.pdf_path.stat().st_size
        
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'keywords': metadata.get('keywords', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'pages': len(self.doc),
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'encrypted': self.doc.is_encrypted
        }


# BACKWARD COMPATIBILITY FUNCTION - Required by main.py
def extract_text_from_pdf(pdf_path: str, language: str = 'en') -> List[str]:
    """
    Extract text from PDF - BACKWARD COMPATIBLE with existing code.
    Thread-safe for use in FastAPI background tasks.
    
    Args:
        pdf_path: Path to PDF file
        language: OCR language code (e.g., 'guj', 'hin', 'mar')
        
    Returns:
        List of extracted text per page
    """
    # Convert Tesseract language codes to ISO if needed
    lang_mapping = {
        'guj': 'gu',
        'hin': 'hi',
        'mar': 'mr',
        'eng': 'en'
    }
    iso_lang = lang_mapping.get(language, language)
    
    reader = PDFReader(pdf_path, iso_lang)
    
    try:
        reader.open()
        pages = reader.extract_all_text()
        
        # Return list of text strings (compatible with old interface)
        return [page['text'] for page in pages]
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise
    
    finally:
        reader.close()


def read_pdf(pdf_path: str, language: str = 'en', progress_callback=None) -> Dict[str, any]:
    """
    Convenience function to read entire PDF with metadata.
    """
    reader = PDFReader(pdf_path, language)
    
    try:
        reader.open()
        metadata = reader.get_metadata()
        pages = reader.extract_all_text(progress_callback)
        
        return {
            'success': True,
            'metadata': metadata,
            'pages': pages,
            'total_pages': len(pages),
            'total_chars': sum(p['char_count'] for p in pages if 'char_count' in p)
        }
        
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        reader.close()


def test_ocr_setup():
    """Test OCR setup and language availability."""
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"✅ Tesseract version: {version}")
        
        langs = pytesseract.get_languages()
        logger.info(f"📚 Available languages: {langs}")
        
        required = ['guj', 'mar', 'hin', 'eng']
        missing = [lang for lang in required if lang not in langs]
        
        if missing:
            logger.warning(f"⚠️  Missing language packs: {missing}")
            return False
        
        logger.info("✅ OCR setup verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ OCR setup test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Testing OCR setup...")
    if test_ocr_setup():
        print("✅ OCR setup OK")
    else:
        print("❌ OCR setup failed")
    
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else 'en'
        
        print(f"\n📖 Reading PDF: {pdf_path}")
        print(f"🌍 Language: {language}")
        
        result = read_pdf(pdf_path, language)
        
        if result['success']:
            print(f"✅ Success!")
            print(f"  Pages: {result['total_pages']}")
            print(f"  Characters: {result['total_chars']}")
        else:
            print(f"❌ Failed: {result['error']}")