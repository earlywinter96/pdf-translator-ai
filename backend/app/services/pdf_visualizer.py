# app/services/pdf_visualizer.py
"""
PDF Visualization Service
-------------------------
Processes English PDFs and creates visual data structures
using Gemini AI for better comprehension
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# ============================================================================
# VISUALIZATION PROCESSOR
# ============================================================================

class PDFVisualizationService:
    """
    Service to convert PDF documents into visual data structures
    """
    
    def __init__(self):
        from app.gemini_wrapper import get_gemini_client
        self.gemini_client = get_gemini_client()
        
        logger.info("🎨 PDF Visualization Service initialized")
    
    def process_pdf(
        self,
        pdf_path: str,
        content_type: Optional[str] = None,
        max_pages: int = 20,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Process PDF and generate visualization data
        
        Args:
            pdf_path: Path to PDF file
            content_type: Type of content (auto-detect if None)
            max_pages: Maximum pages to process (default 20)
            output_format: Output format (json, html, markdown)
            
        Returns:
            Visualization result with data and metadata
        """
        try:
            logger.info(f"🎨 Processing PDF for visualization: {pdf_path}")
            logger.info(f"   Max pages: {max_pages}")
            logger.info(f"   Content type: {content_type or 'auto-detect'}")
            
            # Check file exists
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "error": "PDF file not found"
                }
            
            # Extract text from PDF
            from app.services.pdf_reader import extract_pdf_text_robust, detect_pdf_language
            
            # Detect language first
            detected_lang, confidence = detect_pdf_language(pdf_path)
            logger.info(f"   Detected language: {detected_lang} (confidence: {confidence*100:.0f}%)")

            
            # Only process English PDFs
            if detected_lang not in ["en", "eng"]:
                return {
                    "success": False,
                    "error": f"Only English PDFs supported for visualization (detected: {detected_lang})",
                    "suggestion": "Please use translation feature first to convert to English"
                }
            
            # Extract text
            page_texts, extraction_stats = extract_pdf_text_robust(pdf_path, ocr_language="en")

            
            if not page_texts:
                return {
                    "success": False,
                    "error": "Could not extract text from PDF"
                }
            
            logger.info(f"   Extracted {len(page_texts)} pages")
            logger.info(f"   Total chars: {extraction_stats['total_chars']:,}")
            logger.info(f"   Blank pages: {extraction_stats['blank_pages']}")
            
            # Limit pages
            if len(page_texts) > max_pages:
                logger.warning(f"   ⚠️ Limiting to {max_pages} pages (total: {len(page_texts)})")
                page_texts = page_texts[:max_pages]
            
            # Auto-detect content type if not specified
            if content_type is None:
                sample_text = " ".join(page_texts[:3])
                content_type = self.gemini_client.detect_content_type(sample_text)
            
            logger.info(f"   Content type: {content_type}")
            
            # Generate visualization
            visualization_result = self.gemini_client.visualize_pdf_pages(
                page_texts,
                content_type=content_type,
                max_pages=max_pages
            )
            
            if not visualization_result.get("success"):
                return visualization_result
            
            # Add metadata
            result = {
                "success": True,
                "visualization": visualization_result["data"],
                "metadata": {
                    "total_pages": len(page_texts),
                    "pages_processed": visualization_result.get("pages_processed", len(page_texts)),
                    "content_type": content_type,
                    "model": visualization_result.get("model"),
                    "format": output_format
                }
            }
            
            # Convert to requested format
            if output_format == "html":
                result["html"] = self._generate_html(visualization_result["data"], content_type)
            elif output_format == "markdown":
                result["markdown"] = self._generate_markdown(visualization_result["data"], content_type)
            
            logger.info("✅ Visualization completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Visualization failed: {e}")
            logger.exception(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_html(self, data: Dict[str, Any], content_type: str) -> str:
        """Generate HTML visualization"""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.get('title', 'Document Visualization')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background: #e3f2fd;
            padding: 15px;
            border-left: 4px solid #2196f3;
            margin: 20px 0;
            font-style: italic;
        }}
        .concept-card {{
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }}
        .concept-title {{
            font-weight: bold;
            color: #2980b9;
        }}
        .relationship {{
            display: flex;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #fff3cd;
            border-radius: 5px;
        }}
        .arrow {{
            margin: 0 10px;
            color: #ff6b6b;
        }}
        .timeline-item {{
            border-left: 3px solid #9b59b6;
            padding-left: 20px;
            margin: 15px 0;
        }}
        .data-point {{
            background: #d4edda;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }}
        .tag {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{data.get('title', 'Document Visualization')}</h1>
        <div class="tag">{content_type.title()}</div>
        
        <div class="summary">
            <strong>Summary:</strong> {data.get('summary', data.get('overview', 'No summary available'))}
        </div>
"""
        
        # Add content based on type
        if content_type == "academic":
            html += self._html_academic(data)
        elif content_type == "technical":
            html += self._html_technical(data)
        elif content_type == "educational":
            html += self._html_educational(data)
        else:
            html += self._html_general(data)
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def _html_academic(self, data: Dict) -> str:
        """Generate HTML for academic content"""
        html = ""
        
        # Key concepts
        if "key_concepts" in data:
            html += "<h2>🔑 Key Concepts</h2>"
            for concept in data["key_concepts"]:
                html += f"""
                <div class="concept-card">
                    <div class="concept-title">{concept.get('concept', '')}</div>
                    <p>{concept.get('definition', '')}</p>
                    <em>Importance: {concept.get('importance', '')}</em>
                </div>
                """
        
        # Relationships
        if "relationships" in data:
            html += "<h2>🔗 Relationships</h2>"
            for rel in data["relationships"]:
                html += f"""
                <div class="relationship">
                    <span>{rel.get('from', '')}</span>
                    <span class="arrow">➜ {rel.get('relationship', '')}</span>
                    <span>{rel.get('to', '')}</span>
                </div>
                """
        
        # Timeline
        if "timeline" in data:
            html += "<h2>📅 Timeline</h2>"
            for item in data["timeline"]:
                html += f"""
                <div class="timeline-item">
                    <strong>{item.get('event', '')}</strong>
                    <p>{item.get('significance', '')}</p>
                </div>
                """
        
        return html
    
    def _html_technical(self, data: Dict) -> str:
        """Generate HTML for technical content"""
        html = ""
        
        # Architecture
        if "architecture" in data:
            arch = data["architecture"]
            
            if "components" in arch:
                html += "<h2>🏗️ Components</h2>"
                for comp in arch["components"]:
                    html += f"""
                    <div class="concept-card">
                        <div class="concept-title">{comp.get('name', '')}</div>
                        <p><strong>Type:</strong> {comp.get('type', '')}</p>
                        <p>{comp.get('purpose', '')}</p>
                    </div>
                    """
        
        # Concepts
        if "concepts" in data:
            html += "<h2>💡 Technical Concepts</h2>"
            for concept in data["concepts"]:
                html += f"""
                <div class="concept-card">
                    <div class="concept-title">{concept.get('term', '')}</div>
                    <p>{concept.get('definition', '')}</p>
                    {f'<p><em>Example: {concept.get("example", "")}</em></p>' if concept.get('example') else ''}
                </div>
                """
        
        return html
    
    def _html_educational(self, data: Dict) -> str:
        """Generate HTML for educational content"""
        html = ""
        
        # Learning objectives
        if "learning_objectives" in data:
            html += "<h2>🎯 Learning Objectives</h2><ul>"
            for obj in data["learning_objectives"]:
                html += f"<li>{obj}</li>"
            html += "</ul>"
        
        # Concept map
        if "concept_map" in data:
            cmap = data["concept_map"]
            html += f"<h2>🗺️ Concept Map</h2>"
            html += f"<div class='concept-card'><strong>Central Concept:</strong> {cmap.get('central_concept', '')}</div>"
            
            if "branches" in cmap:
                for branch in cmap["branches"]:
                    html += f"""
                    <div class="concept-card">
                        <div class="concept-title">{branch.get('subtopic', '')}</div>
                        <ul>
                        """
                    for point in branch.get("key_points", []):
                        html += f"<li>{point}</li>"
                    html += "</ul></div>"
        
        return html
    
    def _html_general(self, data: Dict) -> str:
        """Generate HTML for general content"""
        html = ""
        
        # Main ideas
        if "main_ideas" in data:
            html += "<h2>💡 Main Ideas</h2>"
            for idea in data["main_ideas"]:
                html += f"""
                <div class="concept-card">
                    <div class="concept-title">{idea.get('idea', '')}</div>
                    <p>{idea.get('explanation', '')}</p>
                    {f'<div class="tag">{idea.get("visual_suggestion", "")}</div>' if idea.get('visual_suggestion') else ''}
                </div>
                """
        
        # Infographic elements
        if "infographic_elements" in data:
            html += "<h2>📊 Key Information</h2>"
            for elem in data["infographic_elements"]:
                html += f"""
                <div class="data-point">
                    <strong>{elem.get('type', '').title()}:</strong> {elem.get('content', '')}
                </div>
                """
        
        return html
    
    def _generate_markdown(self, data: Dict[str, Any], content_type: str) -> str:
        """Generate Markdown visualization"""
        
        md = f"# {data.get('title', 'Document Visualization')}\n\n"
        md += f"**Content Type:** {content_type.title()}\n\n"
        md += f"## Summary\n\n{data.get('summary', data.get('overview', 'No summary available'))}\n\n"
        
        # Add content based on structure
        for key, value in data.items():
            if key in ['title', 'summary', 'overview']:
                continue
            
            md += f"## {key.replace('_', ' ').title()}\n\n"
            
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            md += f"- **{k}**: {v}\n"
                    else:
                        md += f"- {item}\n"
                md += "\n"
            elif isinstance(value, dict):
                for k, v in value.items():
                    md += f"**{k}**: {v}\n\n"
        
        return md
    
    def save_visualization(
        self,
        visualization_data: Dict[str, Any],
        output_path: str,
        format: str = "json"
    ) -> str:
        """
        Save visualization to file
        
        Args:
            visualization_data: Visualization data
            output_path: Output file path
            format: Output format (json, html, markdown)
            
        Returns:
            Path to saved file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(visualization_data, f, indent=2, ensure_ascii=False)
            
            elif format == "html":
                html_content = visualization_data.get('html', '')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            elif format == "markdown":
                md_content = visualization_data.get('markdown', '')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
            
            logger.info(f"✅ Visualization saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save visualization: {e}")
            raise


# ============================================================================
# SINGLETON
# ============================================================================

_visualizer_service: Optional[PDFVisualizationService] = None

def get_visualizer_service() -> PDFVisualizationService:
    """Get singleton visualizer service"""
    global _visualizer_service
    if _visualizer_service is None:
        _visualizer_service = PDFVisualizationService()
    return _visualizer_service


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def visualize_pdf(
    pdf_path: str,
    content_type: Optional[str] = None,
    max_pages: int = 20,
    output_format: str = "json"
) -> Dict[str, Any]:
    """
    Quick PDF visualization
    
    Args:
        pdf_path: Path to PDF
        content_type: Content type (auto-detect if None)
        max_pages: Max pages to process
        output_format: Output format
        
    Returns:
        Visualization data
    """
    service = get_visualizer_service()
    return service.process_pdf(pdf_path, content_type, max_pages, output_format)