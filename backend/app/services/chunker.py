# app/services/chunker.py
# ============================================================================
# SMART CHUNKER - Better context preservation, no duplicates
# ============================================================================

import re
import logging
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

logger = logging.getLogger(__name__)

CPU_COUNT = multiprocessing.cpu_count()


def chunk_pages_smart(
    pages: List[str], 
    max_words_per_chunk: int = 200,  # Your current setting
    min_words_per_chunk: int = 50,
) -> List[str]:
    """
    Smart chunking with:
    - No duplicate content
    - Better sentence boundary detection
    - Page marker preservation
    - Context awareness
    """
    logger.info(f"🚀 Smart chunking — {len(pages)} pages, max {max_words_per_chunk} words/chunk")
    
    if not pages:
        return []
    
    # Pre-compile patterns
    SENTENCE_END = re.compile(r'([.!?।])\s+')
    PAGE_MARKER = re.compile(r'\[PAGE_\d+\]')
    
    # ====================================================================
    # STEP 1: Process pages with markers
    # ====================================================================
    all_content = []
    
    for idx, page in enumerate(pages):
        if not page.strip():
            continue
        
        # Add page marker at the beginning
        marked_content = f"[PAGE_{idx+1}]\n{page.strip()}"
        all_content.append(marked_content)
    
    # Join all pages
    full_text = "\n\n".join(all_content)
    
    logger.info(f"   Total content: {len(full_text)} chars, {len(full_text.split())} words")
    
    # ====================================================================
    # STEP 2: Split into sentences (preserving page markers)
    # ====================================================================
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences while preserving markers"""
        
        sentences = []
        current = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a page marker
            if PAGE_MARKER.match(line):
                if current:
                    sentences.append(' '.join(current))
                    current = []
                sentences.append(line)  # Add marker as separate item
                continue
            
            # Split line into sentences
            parts = SENTENCE_END.split(line)
            
            for i in range(0, len(parts)-1, 2):
                sentence = parts[i].strip()
                punct = parts[i+1] if i+1 < len(parts) else ''
                
                if sentence:
                    current.append(sentence + punct)
                    
                    # End of sentence - check if we should flush
                    if len(' '.join(current).split()) > 30:  # ~30 words per sentence group
                        sentences.append(' '.join(current))
                        current = []
            
            # Handle last part (no punctuation)
            if len(parts) % 2 == 1 and parts[-1].strip():
                current.append(parts[-1].strip())
        
        # Flush remaining
        if current:
            sentences.append(' '.join(current))
        
        return sentences
    
    sentences = split_into_sentences(full_text)
    logger.info(f"   Split into {len(sentences)} sentence groups")
    
    # ====================================================================
    # STEP 3: Group sentences into chunks
    # ====================================================================
    chunks = []
    current_chunk = []
    current_words = 0
    current_marker = None
    
    for sentence in sentences:
        # Check if it's a page marker
        if PAGE_MARKER.match(sentence):
            # Save current chunk if it exists
            if current_chunk and current_words >= min_words_per_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_words = 0
            
            # Start new chunk with marker
            current_chunk = [sentence]
            current_marker = sentence
            current_words = 0
            continue
        
        # Count words in sentence
        sentence_words = len(sentence.split())
        
        # Check if adding this sentence would exceed limit
        if current_words + sentence_words > max_words_per_chunk and current_words >= min_words_per_chunk:
            # Save current chunk
            chunks.append('\n'.join(current_chunk))
            
            # Start new chunk (with page marker if we have one)
            if current_marker:
                current_chunk = [current_marker, sentence]
            else:
                current_chunk = [sentence]
            
            current_words = sentence_words
        else:
            # Add to current chunk
            current_chunk.append(sentence)
            current_words += sentence_words
    
    # Flush final chunk
    if current_chunk and current_words >= min_words_per_chunk:
        chunks.append('\n'.join(current_chunk))
    elif current_chunk:
        # Too small - merge with previous chunk
        if chunks:
            chunks[-1] = chunks[-1] + '\n' + '\n'.join(current_chunk)
        else:
            chunks.append('\n'.join(current_chunk))
    
    # ====================================================================
    # STEP 4: Validate chunks (remove duplicates)
    # ====================================================================
    seen = set()
    unique_chunks = []
    
    for chunk in chunks:
        # Create a simple hash (first 100 chars)
        chunk_hash = chunk[:100]
        
        if chunk_hash not in seen:
            seen.add(chunk_hash)
            unique_chunks.append(chunk)
        else:
            logger.warning(f"   ⚠️  Skipped duplicate chunk: {chunk[:50]}...")
    
    chunks = unique_chunks
    
    # ====================================================================
    # STEP 5: Statistics
    # ====================================================================
    if chunks:
        sizes = [len(c.split()) for c in chunks]
        
        logger.info(f"✅ Smart chunking complete:")
        logger.info(f"   Chunks: {len(chunks)}")
        logger.info(f"   Words — min: {min(sizes)}, max: {max(sizes)}, avg: {sum(sizes)//len(sizes)}")
    else:
        logger.warning("⚠️  No chunks created!")
    
    return chunks


def reassemble_chunks_smart(
    chunks: List[str], 
    original_page_count: int
) -> List[str]:
    """
    Smart reassembly that respects page markers and prevents duplication
    """
    logger.info(f"🔗 Smart reassembly — {len(chunks)} chunks → {original_page_count} pages")
    
    if not chunks:
        return [''] * original_page_count
    
    # Pre-compile pattern
    PAGE_MARKER = re.compile(r'\[PAGE_(\d+)\]')
    
    # ====================================================================
    # STEP 1: Group chunks by page
    # ====================================================================
    page_contents = {i: [] for i in range(1, original_page_count + 1)}
    current_page = 1
    
    for chunk in chunks:
        # Find all page markers in this chunk
        markers = [(m.group(1), m.start()) for m in PAGE_MARKER.finditer(chunk)]
        
        if not markers:
            # No markers - add to current page
            # Remove any stray markers first
            clean_chunk = PAGE_MARKER.sub('', chunk).strip()
            if clean_chunk:
                page_contents[current_page].append(clean_chunk)
        else:
            # Has markers - split by markers
            for i, (page_num, pos) in enumerate(markers):
                page_num = int(page_num)
                
                # Get content after this marker (until next marker or end)
                start = pos + len(f'[PAGE_{page_num}]')
                end = markers[i+1][1] if i+1 < len(markers) else len(chunk)
                
                content = chunk[start:end].strip()
                
                if content and page_num <= original_page_count:
                    page_contents[page_num].append(content)
                    current_page = page_num
    
    # ====================================================================
    # STEP 2: Assemble pages
    # ====================================================================
    pages = []
    
    for page_num in range(1, original_page_count + 1):
        content_parts = page_contents[page_num]
        
        if content_parts:
            # Join with paragraph breaks
            page_text = '\n\n'.join(content_parts)
        else:
            page_text = ''
        
        pages.append(page_text)
    
    logger.info(f"   ✅ Reassembled {len(pages)} pages")
    
    return pages


# ============================================================================
# BACKWARDS COMPATIBILITY
# ============================================================================

def chunk_pages_ultra_fast(pages: List[str], max_words_per_chunk: int = 200, **kwargs):
    """Alias for backwards compatibility"""
    return chunk_pages_smart(pages, max_words_per_chunk=max_words_per_chunk)

def reassemble_chunks_ultra_fast(chunks: List[str], original_page_count: int):
    """Alias for backwards compatibility"""
    return reassemble_chunks_smart(chunks, original_page_count)