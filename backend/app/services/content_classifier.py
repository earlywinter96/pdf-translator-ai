# app/services/content_classifier.py
"""
Intelligent Content Classifier
------------------------------
Classifies text content to route to the best translation model:
- Body text → IndicTrans (fast & free)
- Complex/structured → GPT (quality)
"""

import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# CONTENT TYPES
# ============================================================================

@dataclass
class ContentSegment:
    """A classified segment of text"""
    text: str
    content_type: str
    confidence: float
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContentType:
    """Content type constants"""
    BODY_TEXT = "body_text"          # Regular paragraphs
    HEADING = "heading"               # Titles, headers
    LIST = "simple_list"              # Bullet points
    QUESTION = "question"             # Questions, exercises
    COMPLEX = "complex"               # Poetry, idioms, cultural
    TABLE = "table"                   # Tabular data
    TECHNICAL = "technical"           # Technical terminology
    SONG = "song"                     # Songs, verses
    EXERCISE = "exercise"             # Educational exercises


# ============================================================================
# CONTENT CLASSIFIER
# ============================================================================

class ContentClassifier:
    """
    Classifies text into content types for optimal translation routing
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for content detection"""
        
        # Structured markers (from original chunker)
        self.marker_patterns = {
            'song': re.compile(r'\[SONG\].*?\[/SONG\]', re.DOTALL | re.IGNORECASE),
            'question': re.compile(r'\[QUESTION\].*?\[/QUESTION\]', re.DOTALL | re.IGNORECASE),
            'exercise': re.compile(r'\[EXERCISE\].*?\[/EXERCISE\]', re.DOTALL | re.IGNORECASE),
            'heading': re.compile(r'\[HEADING\].*?\[/HEADING\]', re.DOTALL | re.IGNORECASE),
            'activity': re.compile(r'\[ACTIVITY\].*?\[/ACTIVITY\]', re.DOTALL | re.IGNORECASE),
        }
        
        # List patterns
        self.list_patterns = [
            re.compile(r'^\s*[•●○■□▪▫✓✔➢⇒→]\s+', re.MULTILINE),  # Bullet points
            re.compile(r'^\s*\d+\.\s+', re.MULTILINE),             # Numbered lists
            re.compile(r'^\s*[a-z]\.\s+', re.MULTILINE),           # Letter lists
            re.compile(r'^\s*\([a-z]\)\s+', re.MULTILINE),         # (a) style
        ]
        
        # Question patterns
        self.question_patterns = [
            re.compile(r'\?\s*$', re.MULTILINE),                   # Ends with ?
            re.compile(r'^(what|when|where|why|how|which|who)\s+', re.IGNORECASE),
            re.compile(r'(discuss|explain|analyze|describe|compare)\b', re.IGNORECASE),
        ]
        
        # Technical patterns
        self.technical_patterns = [
            re.compile(r'\b(algorithm|function|variable|class|method|api|database)\b', re.IGNORECASE),
            re.compile(r'\b(equation|formula|theorem|proof)\b', re.IGNORECASE),
            re.compile(r'[A-Za-z]+\([^)]*\)'),  # Function calls
            re.compile(r'\b[A-Z]{2,}\b'),        # UPPERCASE terms
        ]
    
    def classify_text(self, text: str) -> str:
        """
        Classify a piece of text into its primary content type
        
        Args:
            text: Text to classify
            
        Returns:
            Content type string
        """
        if not text or not text.strip():
            return ContentType.BODY_TEXT
        
        text_clean = text.strip()
        
        # Check for structured markers first (highest priority)
        for marker_type, pattern in self.marker_patterns.items():
            if pattern.search(text):
                logger.debug(f"   Classified as {marker_type} (marker detected)")
                return marker_type
        
        # Check for headings (short, possibly uppercase)
        if self._is_heading(text_clean):
            return ContentType.HEADING
        
        # Check for lists
        if self._is_list(text_clean):
            return ContentType.LIST
        
        # Check for questions
        if self._is_question(text_clean):
            return ContentType.QUESTION
        
        # Check for technical content
        if self._is_technical(text_clean):
            return ContentType.TECHNICAL
        
        # Check for complex content (poetry, cultural references)
        if self._is_complex(text_clean):
            return ContentType.COMPLEX
        
        # Default: body text (90% of content should be this)
        return ContentType.BODY_TEXT
    
    def _is_heading(self, text: str) -> bool:
        """Check if text is a heading"""
        # Short text (< 100 chars)
        if len(text) > 100:
            return False
        
        # No periods (headings rarely have periods)
        if '.' in text and not text.endswith('.'):
            return False
        
        # Single line
        if '\n' in text:
            return False
        
        # Mostly uppercase or title case
        words = text.split()
        if len(words) > 0:
            title_case = sum(1 for w in words if w and w[0].isupper()) / len(words)
            if title_case > 0.7 or text.isupper():
                return True
        
        # Check for heading indicators
        heading_words = ['chapter', 'lesson', 'unit', 'section', 'part', 'activity']
        if any(word in text.lower() for word in heading_words):
            return True
        
        return False
    
    def _is_list(self, text: str) -> bool:
        """Check if text is a list"""
        lines = text.split('\n')
        
        # Need at least 2 items
        if len(lines) < 2:
            return False
        
        # Check for list markers
        for pattern in self.list_patterns:
            matches = pattern.findall(text)
            if len(matches) >= 2:  # At least 2 items with same marker
                return True
        
        return False
    
    def _is_question(self, text: str) -> bool:
        """Check if text contains questions"""
        # Check for question marks
        if text.count('?') >= 1:
            return True
        
        # Check for question patterns
        for pattern in self.question_patterns:
            if pattern.search(text):
                return True
        
        # Check for exercise keywords
        exercise_words = ['discuss', 'explain', 'analyze', 'describe', 'answer']
        if any(word in text.lower() for word in exercise_words):
            return True
        
        return False
    
    def _is_technical(self, text: str) -> bool:
        """Check if text is technical"""
        # Check for technical patterns
        technical_score = 0
        for pattern in self.technical_patterns:
            matches = pattern.findall(text)
            technical_score += len(matches)
        
        # If >10% of words are technical terms
        words = text.split()
        if len(words) > 0 and technical_score / len(words) > 0.10:
            return True
        
        return False
    
    def _is_complex(self, text: str) -> bool:
        """Check if text is complex (poetry, idioms, cultural)"""
        # Short poetic lines
        lines = text.split('\n')
        if len(lines) >= 3:
            avg_line_length = sum(len(l.strip()) for l in lines) / len(lines)
            if avg_line_length < 50:  # Short lines = potential poetry
                return True
        
        # Rhyme scheme detection (basic)
        if self._has_rhyme_scheme(text):
            return True
        
        # Cultural keywords
        cultural_words = ['tradition', 'festival', 'ritual', 'custom', 'folk', 'moral']
        if sum(1 for word in cultural_words if word in text.lower()) >= 2:
            return True
        
        # Repetitive structure (common in songs)
        if self._has_repetitive_structure(text):
            return True
        
        return False
    
    def _has_rhyme_scheme(self, text: str) -> bool:
        """Check for basic rhyme scheme (oversimplified)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) < 3:
            return False
        
        # Check if lines end with similar sounds (very basic)
        endings = [line.split()[-1][-3:] if line.split() else '' for line in lines]
        unique_endings = set(endings)
        
        # If many lines share endings, might be poetry
        if len(unique_endings) < len(endings) * 0.6:
            return True
        
        return False
    
    def _has_repetitive_structure(self, text: str) -> bool:
        """Check for repetitive structure (songs, chants)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) < 4:
            return False
        
        # Check if any line repeats
        line_counts = {}
        for line in lines:
            line_counts[line] = line_counts.get(line, 0) + 1
        
        # If any line repeats 2+ times, probably a song
        if any(count >= 2 for count in line_counts.values()):
            return True
        
        return False
    
    def classify_chunks(self, chunks: List[str]) -> List[ContentSegment]:
        """
        Classify multiple text chunks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of classified segments
        """
        segments = []
        
        for i, chunk in enumerate(chunks):
            content_type = self.classify_text(chunk)
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(chunk, content_type)
            
            segment = ContentSegment(
                text=chunk,
                content_type=content_type,
                confidence=confidence,
                metadata={'chunk_index': i}
            )
            
            segments.append(segment)
            
            logger.debug(f"Chunk {i+1}: {content_type} (confidence: {confidence:.2f})")
        
        return segments
    
    def _calculate_confidence(self, text: str, content_type: str) -> float:
        """
        Calculate classification confidence
        
        Args:
            text: Classified text
            content_type: Assigned content type
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Base confidence
        confidence = 0.70
        
        # Increase confidence for strong indicators
        if content_type in ['song', 'question', 'exercise', 'heading']:
            # Has explicit markers
            for pattern in self.marker_patterns.values():
                if pattern.search(text):
                    confidence = 0.95
                    break
        
        if content_type == ContentType.HEADING:
            if text.isupper() or len(text) < 50:
                confidence = 0.90
        
        if content_type == ContentType.LIST:
            # Count list items
            list_items = sum(1 for p in self.list_patterns for _ in p.findall(text))
            if list_items >= 3:
                confidence = 0.90
        
        if content_type == ContentType.QUESTION:
            if text.count('?') >= 2:
                confidence = 0.90
        
        return confidence
    
    def get_statistics(self, segments: List[ContentSegment]) -> Dict:
        """
        Get classification statistics
        
        Args:
            segments: List of classified segments
            
        Returns:
            Statistics dictionary
        """
        total = len(segments)
        if total == 0:
            return {}
        
        # Count by type
        type_counts = {}
        for segment in segments:
            type_counts[segment.content_type] = type_counts.get(segment.content_type, 0) + 1
        
        # Calculate percentages
        type_percentages = {
            content_type: (count / total) * 100
            for content_type, count in type_counts.items()
        }
        
        # Average confidence
        avg_confidence = sum(s.confidence for s in segments) / total
        
        return {
            'total_segments': total,
            'type_counts': type_counts,
            'type_percentages': type_percentages,
            'avg_confidence': avg_confidence,
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def classify_single(text: str) -> str:
    """
    Quick classification of a single text
    
    Args:
        text: Text to classify
        
    Returns:
        Content type
    """
    classifier = ContentClassifier()
    return classifier.classify_text(text)


def should_use_gpt(text: str) -> bool:
    """
    Determine if text should use GPT instead of IndicTrans
    
    Args:
        text: Text to check
        
    Returns:
        True if GPT is recommended
    """
    classifier = ContentClassifier()
    content_type = classifier.classify_text(text)
    
    # These types need GPT for best quality
    gpt_types = [
        ContentType.HEADING,
        ContentType.QUESTION,
        ContentType.COMPLEX,
        ContentType.SONG,
        ContentType.EXERCISE,
    ]
    
    return content_type in gpt_types


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test classifier
    classifier = ContentClassifier()
    
    test_texts = [
        ("This is a regular paragraph with normal text.", ContentType.BODY_TEXT),
        ("CHAPTER 1: INTRODUCTION", ContentType.HEADING),
        ("• First item\n• Second item\n• Third item", ContentType.LIST),
        ("What is the capital of India? Explain your answer.", ContentType.QUESTION),
        ("[SONG]\nRow row row your boat\nGently down the stream\n[/SONG]", 'song'),
    ]
    
    print("\n" + "=" * 70)
    print("CONTENT CLASSIFIER TESTS")
    print("=" * 70)
    
    for text, expected in test_texts:
        result = classifier.classify_text(text)
        status = "✅" if result == expected else "❌"
        print(f"\n{status} Text: {text[:50]}...")
        print(f"   Expected: {expected}")
        print(f"   Got: {result}")
    
    print("\n" + "=" * 70)