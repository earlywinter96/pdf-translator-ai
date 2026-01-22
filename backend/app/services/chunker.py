"""
Text Chunking Service
---------------------
Responsibility:
- Combine all pages
- Chunk across the entire document
- Keep chunks GPT-safe
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

MAX_WORDS_PER_CHUNK = 900


class ChunkingError(Exception):
    pass


def chunk_pages(
    pages: List[str],
    max_words: int = MAX_WORDS_PER_CHUNK
) -> List[str]:
    """
    Chunk full PDF text into translation-safe chunks.
    Chunking is done ACROSS pages, not per page.
    """

    if not pages:
        raise ChunkingError("No pages provided for chunking")

    # 1️⃣ Combine all pages into one stream
    full_text = "\n\n".join(
        page.strip() for page in pages if page and page.strip()
    )

    if not full_text.strip():
        raise ChunkingError("PDF contains no extractable text")

    # 2️⃣ Split by paragraphs
    paragraphs = [
        p.strip() for p in full_text.split("\n\n") if p.strip()
    ]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_word_count = 0

    for para in paragraphs:
        words = para.split()
        word_count = len(words)

        # 3️⃣ Split very large paragraph
        if word_count > max_words:
            for i in range(0, word_count, max_words):
                chunks.append(" ".join(words[i:i + max_words]))
            continue

        # 4️⃣ Normal accumulation
        if current_word_count + word_count <= max_words:
            current_chunk.append(para)
            current_word_count += word_count
        else:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_word_count = word_count

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    logger.info(
        "Total chunks created from PDF: %d",
        len(chunks)
    )

    return chunks
