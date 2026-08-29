# app/gemini_wrapper.py
"""
Gemini API Wrapper for PDF Visualization
-----------------------------------------
Uses Google Gemini to convert English text PDFs into visual data structures
Inspired by PaperBanana's approach to academic paper visualization
"""

import os
import logging
import json          # ← move it here
import time
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Gemini retired this model. Keep existing deployments working even when they
# still have the old name configured in Render's environment variables.
if GEMINI_MODEL.removeprefix("models/") == "gemini-2.0-flash-lite":
    logger.warning("GEMINI_MODEL gemini-2.0-flash-lite was retired; using gemini-3.5-flash-lite")
    GEMINI_MODEL = "gemini-3.5-flash-lite"

MAX_PAGES_FOR_VISUALIZATION = int(os.getenv("MAX_PAGES_FOR_VISUALIZATION", "20"))

# Visualization templates
VISUALIZATION_PROMPTS = {
    "academic": """You are a visual learning expert. Analyze this academic/research text and create a comprehensive visual data structure.

REQUIRED OUTPUT FORMAT (JSON):
{{
  "title": "Document title",
  "summary": "2-3 sentence overview",
  "key_concepts": [
    {{"concept": "name", "definition": "brief explanation", "importance": "why it matters"}}
  ],
  "visual_structure": {{
    "main_sections": [
      {{
        "title": "Section name",
        "key_points": ["point 1", "point 2"],
        "diagrams": [{{"type": "flowchart/mindmap/timeline", "description": "what to show"}}]
      }}
    ]
  }},
  "relationships": [
    {{"from": "concept A", "to": "concept B", "relationship": "causes/enables/requires"}}
  ],
  "timeline": [
    {{"event": "description", "significance": "why important"}}
  ],
  "data_points": [
    {{"metric": "name", "value": "value", "context": "what it means"}}
  ]
}}

Text to analyze:
{text}

Create a rich, visual-first representation that makes this content easy to understand at a glance.""",

    "general": """You are a visual communication expert. Transform this text into an engaging visual data structure.

REQUIRED OUTPUT FORMAT (JSON):
{{
  "title": "Document title",
  "summary": "Brief overview",
  "main_ideas": [
    {{"idea": "concept", "explanation": "simple explanation", "visual_suggestion": "diagram type"}}
  ],
  "structure": {{
    "hierarchy": [
      {{
        "level": "1-3",
        "title": "section",
        "content": ["key point 1", "key point 2"]
      }}
    ]
  }},
  "infographic_elements": [
    {{"type": "stat/quote/fact", "content": "the content", "visual_type": "icon/chart/callout"}}
  ],
  "connections": [
    {{"item1": "A", "item2": "B", "connection": "relationship"}}
  ]
}}

Text to analyze:
{text}

Focus on making complex information simple and visually engaging.""",

    "technical": """You are a technical documentation expert. Create a visual architecture of this technical content.

REQUIRED OUTPUT FORMAT (JSON):
{{
  "title": "Document title",
  "overview": "Technical summary",
  "architecture": {{
    "components": [
      {{"name": "component", "purpose": "what it does", "type": "module/service/function"}}
    ],
    "flows": [
      {{"process": "name", "steps": ["step 1", "step 2"], "diagram_type": "sequence/flow"}}
    ]
  }},
  "concepts": [
    {{"term": "technical term", "definition": "explanation", "example": "use case"}}
  ],
  "diagrams": [
    {{"type": "architecture/sequence/state", "description": "what to show", "elements": ["element 1"]}}
  ],
  "code_structures": [
    {{"structure": "pattern/algorithm", "visualization": "how to represent visually"}}
  ]
}}

Text to analyze:
{text}

Create technical diagrams and architectural views that clarify complex systems.""",

    "educational": """You are an educational content designer. Transform this educational content into visual learning materials.

REQUIRED OUTPUT FORMAT (JSON):
{{
  "title": "Lesson/Topic title",
  "learning_objectives": ["objective 1", "objective 2"],
  "concept_map": {{
    "central_concept": "main topic",
    "branches": [
      {{
        "subtopic": "name",
        "key_points": ["point 1", "point 2"],
        "examples": ["example 1"]
      }}
    ]
  }},
  "visual_aids": [
    {{"type": "diagram/illustration/chart", "purpose": "what it teaches", "description": "content"}}
  ],
  "step_by_step": [
    {{"step": 1, "action": "what to do", "visual": "diagram suggestion"}}
  ],
  "key_takeaways": [
    {{"takeaway": "main point", "visual_representation": "how to show it"}}
  ]
}}

Text to analyze:
{text}

Design visual learning materials that enhance comprehension and retention."""
}


# ============================================================================
# GEMINI CLIENT
# ============================================================================

class GeminiVisualizationClient:
    """
    Google Gemini client for PDF visualization
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.model_name = model
        
        # Configure Gemini
        #genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.client = genai.Client(api_key=self.api_key)

        
        logger.info(f"✅ Gemini client initialized - model: {self.model_name}")
    
    def visualize_text(
        self,
        text: str,
        content_type: str = "general",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Convert text into visual data structure
        
        Args:
            text: Text content to visualize
            content_type: Type of content (academic, general, technical, educational)
            max_retries: Maximum retry attempts
            
        Returns:
            Dictionary with visualization data
        """
        if not text or not text.strip():
            return {"error": "Empty text provided"}
        
        # Select appropriate prompt
        prompt_template = VISUALIZATION_PROMPTS.get(
            content_type,
            VISUALIZATION_PROMPTS["general"]
        )
        
        prompt = prompt_template.format(text=text[:10000])  # Limit text length
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🎨 Generating visualization (attempt {attempt}/{max_retries})...")
                
                # Generate content
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.4,  # More focused/consistent
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    }
                )
                
                # Extract text
                result_text = response.text.strip() if response.text else ""

                
                
                # Remove markdown code blocks if present
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                
                result_text = result_text.strip()
                
                # Parse JSON
                visualization_data = json.loads(result_text)
                
                logger.info("✅ Visualization generated successfully")
                
                return {
                    "success": True,
                    "data": visualization_data,
                    "content_type": content_type,
                    "model": self.model_name
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parse error (attempt {attempt}): {e}")
                if attempt == max_retries:
                    # Return raw text if JSON parsing fails
                    return {
                        "success": False,
                        "error": "Could not parse visualization data",
                        "raw_text": result_text[:500]
                    }
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Visualization error (attempt {attempt}): {e}")
                if attempt == max_retries:
                    return {
                        "success": False,
                        "error": str(e)
                    }
                time.sleep(2)
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def visualize_pdf_pages(
        self,
        page_texts: List[str],
        content_type: str = "general",
        max_pages: int = MAX_PAGES_FOR_VISUALIZATION
    ) -> Dict[str, Any]:
        """
        Visualize multiple PDF pages
        
        Args:
            page_texts: List of page text contents
            content_type: Type of content
            max_pages: Maximum pages to process
            
        Returns:
            Comprehensive visualization data
        """
        if not page_texts:
            return {"error": "No pages provided"}
        
        # Limit pages
        if len(page_texts) > max_pages:
            logger.warning(f"⚠️ Limiting to first {max_pages} pages (got {len(page_texts)})")
            page_texts = page_texts[:max_pages]
        
        # Combine all pages
        combined_text = "\n\n".join(page_texts)
        
        logger.info(f"📊 Visualizing {len(page_texts)} pages ({len(combined_text)} chars)...")
        
        # Generate visualization
        result = self.visualize_text(combined_text, content_type)
        
        if result.get("success"):
            result["pages_processed"] = len(page_texts)
            result["total_characters"] = len(combined_text)
        
        return result
    
    def visualize_pdf_file(
        self,
        pdf_path: str,
        content_type: str = "general",
        max_pages: int = MAX_PAGES_FOR_VISUALIZATION
    ) -> Dict[str, Any]:
        """
        Visualize PDF file directly
        
        Args:
            pdf_path: Path to PDF file
            content_type: Type of content
            max_pages: Maximum pages to process
            
        Returns:
            Visualization data
        """
        try:
            # Extract text from PDF
            from app.services.pdf_reader import extract_pdf_text_robust
            
            logger.info(f"📄 Reading PDF: {pdf_path}")
            page_texts = extract_pdf_text_robust(pdf_path)
            
            if not page_texts:
                return {"error": "Could not extract text from PDF"}
            
            # Visualize
            return self.visualize_pdf_pages(page_texts, content_type, max_pages)
            
        except Exception as e:
            logger.error(f"❌ PDF visualization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def detect_content_type(self, text: str) -> str:
        """
        Auto-detect content type from text
        
        Args:
            text: Sample text
            
        Returns:
            Content type (academic, general, technical, educational)
        """
        text_lower = text.lower()
        
        # Academic indicators
        academic_keywords = [
            "abstract", "methodology", "research", "study", "findings",
            "hypothesis", "experiment", "analysis", "conclusion", "references"
        ]
        
        # Technical indicators
        technical_keywords = [
            "function", "algorithm", "implementation", "system", "architecture",
            "api", "database", "server", "code", "framework", "module"
        ]
        
        # Educational indicators
        educational_keywords = [
            "lesson", "chapter", "exercise", "learning", "student",
            "objective", "quiz", "homework", "practice", "tutorial"
        ]
        
        # Count keyword matches
        academic_score = sum(1 for kw in academic_keywords if kw in text_lower)
        technical_score = sum(1 for kw in technical_keywords if kw in text_lower)
        educational_score = sum(1 for kw in educational_keywords if kw in text_lower)
        
        # Determine type
        scores = {
            "academic": academic_score,
            "technical": technical_score,
            "educational": educational_score
        }
        
        max_score = max(scores.values())
        
        if max_score >= 3:
            content_type = max(scores, key=scores.get)
            logger.info(f"🎯 Auto-detected content type: {content_type}")
            return content_type
        
        logger.info("🎯 Using general content type (default)")
        return "general"


# ============================================================================
# SINGLETON
# ============================================================================

_gemini_client: Optional[GeminiVisualizationClient] = None

def get_gemini_client() -> GeminiVisualizationClient:
    """Get singleton Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiVisualizationClient()
    return _gemini_client


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def visualize_pdf_quick(
    pdf_path: str,
    content_type: Optional[str] = None,
    max_pages: int = MAX_PAGES_FOR_VISUALIZATION
) -> Dict[str, Any]:
    """
    Quick PDF visualization
    
    Args:
        pdf_path: Path to PDF
        content_type: Content type (auto-detect if None)
        max_pages: Max pages to process
        
    Returns:
        Visualization data
    """
    client = get_gemini_client()
    
    # Auto-detect content type if not provided
    if content_type is None:
        from app.services.pdf_reader import extract_pdf_text_robust
        page_texts = extract_pdf_text_robust(pdf_path)
        if page_texts:
            sample_text = " ".join(page_texts[:3])  # First 3 pages
            content_type = client.detect_content_type(sample_text)
        else:
            content_type = "general"
    
    return client.visualize_pdf_file(pdf_path, content_type, max_pages)


# ============================================================================
# USAGE TRACKER (Optional)
# ============================================================================

def track_gemini_usage(characters: int, model: str):
    """Track Gemini API usage for cost monitoring"""
    try:
        usage_file = "gemini_usage.json"
        
        import json
        from datetime import datetime
        
        # Load existing usage
        if os.path.exists(usage_file):
            with open(usage_file, 'r') as f:
                usage = json.load(f)
        else:
            usage = {
                "total_characters": 0,
                "total_requests": 0,
                "by_model": {},
                "last_updated": None
            }
        
        # Update usage
        usage["total_characters"] += characters
        usage["total_requests"] += 1
        usage["last_updated"] = datetime.now().isoformat()
        
        if model not in usage["by_model"]:
            usage["by_model"][model] = {"characters": 0, "requests": 0}
        
        usage["by_model"][model]["characters"] += characters
        usage["by_model"][model]["requests"] += 1
        
        # Save
        with open(usage_file, 'w') as f:
            json.dump(usage, f, indent=2)
        
        logger.debug(f"📊 Gemini usage tracked: {characters} chars")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not track usage: {e}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("GEMINI VISUALIZATION CLIENT TEST")
    print("=" * 70)
    
    # Test text visualization
    sample_text = """
    Machine Learning Overview
    
    Machine learning is a subset of artificial intelligence that enables systems
    to learn and improve from experience without being explicitly programmed.
    
    Key Concepts:
    1. Supervised Learning - Learning from labeled data
    2. Unsupervised Learning - Finding patterns in unlabeled data
    3. Reinforcement Learning - Learning through trial and error
    
    Applications include image recognition, natural language processing,
    and predictive analytics.
    """
    
    try:
        client = get_gemini_client()
        
        print("\n🎨 Testing text visualization...")
        result = client.visualize_text(sample_text, "technical")
        
        if result.get("success"):
            print("\n✅ Visualization successful!")
            print(f"\nData structure:")
            import json
            print(json.dumps(result["data"], indent=2))
        else:
            print(f"\n❌ Visualization failed: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "=" * 70)
