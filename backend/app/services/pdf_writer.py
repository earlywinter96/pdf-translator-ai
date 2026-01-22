"""
PDF Writer Service
------------------
Responsibility:
- Generate an English PDF from translated text
- Handle large documents safely
- Maintain readable formatting
"""

from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
import logging
import os


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFWriteError(Exception):
    """Custom exception for PDF writing errors"""
    pass


def create_pdf_from_text(
    translated_chunks: List[str],
    output_path: str,
    title: str = "Translated Document"
) -> str:
    """
    Create a PDF from translated text chunks.

    Args:
        translated_chunks (List[str]): List of translated text chunks
        output_path (str): Output PDF file path
        title (str): PDF title

    Returns:
        str: Path to generated PDF
    """

    if not translated_chunks:
        raise PDFWriteError("No translated text provided")

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()

        body_style = ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=12
        )

        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=20
        )

        story = []

        # Title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Body text
        for chunk in translated_chunks:
            paragraphs = chunk.split("\n")
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
                else:
                    story.append(Spacer(1, 0.15 * inch))

        doc.build(story)

        logger.info(f"PDF generated successfully at {output_path}")
        return output_path

    except Exception as e:
        logger.exception("Failed to generate PDF")
        raise PDFWriteError(f"PDF generation failed: {str(e)}")
