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


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFReadError(Exception):
    pass


# OCR languages (Gujarati + Marathi + Hindi)
def _ocr_page(image: Image.Image, ocr_lang: str) -> str:
    try:
        text = pytesseract.image_to_string(
            image,
            lang=ocr_lang,
            config="--psm 6"
        )
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""


def extract_text_from_pdf(pdf_path: str, ocr_lang: str) -> List[str]:
    """
    Extract text from PDF pages.
    Uses OCR ONLY when extracted text is insufficient.
    """

    MIN_TEXT_LENGTH = 60  # 🔑 critical threshold
    pages_text: List[str] = []

    if not os.path.exists(pdf_path):
        raise PDFReadError("PDF file does not exist")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF opened successfully. Pages: {total_pages}")

            for page_number, page in enumerate(pdf.pages, start=1):
                text = ""

                try:
                    # 1️⃣ Try normal text extraction
                    extracted = page.extract_text() or ""
                    text = extracted.strip()

                except Exception as e:
                    logger.warning(
                        f"Text extraction failed on page {page_number}: {e}"
                    )

                # 2️⃣ OCR fallback ONLY if text is insufficient
                if len(text) < MIN_TEXT_LENGTH:
                    logger.info(f"Using OCR for page {page_number}")

                    with tempfile.TemporaryDirectory() as temp_dir:
                        images = convert_from_path(
                            pdf_path,
                            first_page=page_number,
                            last_page=page_number,
                            dpi=250,  # 🔹 faster, still accurate
                            output_folder=temp_dir
                        )

                        if images:
                            text = _ocr_page(images[0], ocr_lang).strip()

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
                    pages_text.append("")

    except Exception as e:
        logger.exception("Failed to read PDF")
        raise PDFReadError(str(e))

    if not any(pages_text):
        raise PDFReadError("No extractable text found (OCR also failed)")

    logger.info("PDF text extraction (hybrid OCR) completed successfully")
    return pages_text
