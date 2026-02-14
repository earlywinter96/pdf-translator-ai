"""
LipiTranslate - AI-Powered PDF Translation - IMPROVED VERSION
==============================================================
Main FastAPI application with enhanced validation, error handling,
and language detection
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid

# Import improved services
from app.services.pdf_reader import (
    extract_pdf_text_robust,
    detect_pdf_language,
    validate_language_match,
    get_non_blank_pages
)
from app.services.hybrid_translator import HybridTranslatorV2
from app.services.pdf_writer import create_translated_pdf
from app.sarvam_wrapper import SarvamTranslator
from app.openai_wrapper import OpenAITranslator

# Import existing modules
from app.models.job import (
    create_job,
    update_job,
    complete_job,
    fail_job,
    get_job,
    cleanup_old_jobs,
    start_cleanup_scheduler
)
from app.payment import payment_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "outputs")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Create directories
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 LipiTranslate Starting Up (IMPROVED)")
    logger.info("=" * 70)
    logger.info("📊 Configuration:")
    logger.info(f"   Uploads: {UPLOADS_DIR}")
    logger.info(f"   Outputs: {OUTPUTS_DIR}")
    logger.info(f"   Max file size: {MAX_FILE_SIZE_MB}MB")
    logger.info(f"   Primary translator: Sarvam AI")
    logger.info(f"   Fallback translator: OpenAI GPT-4o")
    logger.info(f"   Features: Language validation, blank page detection")
    
    # Start background schedulers
    start_cleanup_scheduler()
    # Uncomment when payment session cleanup is implemented
    # start_session_cleanup_scheduler()
    
    logger.info("=" * 70)
    logger.info("✅ Application ready")
    logger.info("=" * 70)
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="LipiTranslate",
    description="AI-Powered PDF Translation with Enhanced Validation",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.lipitranslate.in",
        "https://lipitranslate.in",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include payment routes
app.include_router(payment_router)


# ============================================================================
# LANGUAGE DETECTION ENDPOINT
# ============================================================================

@app.post("/api/detect-language")
async def detect_language_endpoint(file: UploadFile = File(...)):
    """
    Detect the language of a PDF
    
    Args:
        file: PDF file
        
    Returns:
        Detected language and confidence
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Save temporary file
    temp_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOADS_DIR, f"temp_{temp_id}.pdf")
    
    try:
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Detect language
        detected_lang, confidence = detect_pdf_language(temp_path)
        
        return {
            "detected": detected_lang,
            "confidence": confidence,
            "message": f"Detected {detected_lang} with {confidence*100:.0f}% confidence"
        }
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/check-pdf-pages")
async def check_pdf_pages(file: UploadFile = File(...)):
    """
    Check PDF page count and language for visualization eligibility
    
    Args:
        file: PDF file
        
    Returns:
        PDF metadata including page count, language, and visualization availability
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Save temporary file
    temp_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOADS_DIR, f"temp_{temp_id}.pdf")
    
    try:
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                413,
                f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
            )
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Extract text to get page count
        import PyPDF2
        with open(temp_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            page_count = len(pdf_reader.pages)
        
        # Detect language
        detected_lang, confidence = detect_pdf_language(temp_path)
        
        # Check if visualization is available
        # Only English PDFs with <= 20 pages can be visualized
        MAX_VIZ_PAGES = 20
        is_english = detected_lang in ['en', 'eng', 'english']
        visualization_available = is_english and page_count <= MAX_VIZ_PAGES
        
        visualization_note = None
        if not is_english:
            visualization_note = "Only English PDFs can be visualized. Please translate to English first."
        elif page_count > MAX_VIZ_PAGES:
            visualization_note = f"PDF has {page_count} pages. Visualization is limited to {MAX_VIZ_PAGES} pages."
        
        return {
            "page_count": page_count,
            "detected_language": detected_lang,
            "confidence": confidence,
            "visualization_available": visualization_available,
            "visualization_note": visualization_note,
            "file_size": len(content)
        }
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ============================================================================
# TRANSLATION ENDPOINTS
# ============================================================================

@app.post("/api/translate")
async def translate_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...)
):
    """
    Translate a PDF file with language validation
    
    Args:
        file: PDF file to translate
        source_language: Source language (gujarati, hindi, marathi, english, etc.)
        target_language: Target language
        
    Returns:
        Job ID for tracking translation progress
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Read file content
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            413,
            f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    with open(input_path, 'wb') as f:
        f.write(content)
    
    # Create job
    create_job(job_id, file.filename, "translation")
    
    # Start translation in background
    background_tasks.add_task(
        translate_pdf_task,
        job_id,
        input_path,
        source_language,
        target_language
    )
    
    logger.info(f"📤 Translation job created: {job_id}")
    logger.info(f"   File: {file.filename}")
    logger.info(f"   {source_language} → {target_language}")
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Translation started"
    }


@app.get("/api/status/{job_id}")
async def get_translation_status(job_id: str):
    """
    Get translation job status
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status and progress
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "output_path": job.get("output_path")
    }


@app.get("/api/download/{job_id}")
async def download_translated_pdf(job_id: str):
    """
    Download translated PDF
    
    Args:
        job_id: Job identifier
        
    Returns:
        Translated PDF file
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Translation not completed yet")
    
    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(404, "Translated file not found")
    
    original_filename = job.get("original_filename", "document.pdf")
    base_name = os.path.splitext(original_filename)[0]
    download_filename = f"{base_name}_translated.pdf"
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=download_filename
    )


@app.get("/api/preview/original/{job_id}")
async def preview_original_pdf(job_id: str):
    """
    Preview original PDF in browser
    
    Args:
        job_id: Job identifier
        
    Returns:
        Original PDF file for inline viewing
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Original file path
    input_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    
    if not os.path.exists(input_path):
        raise HTTPException(404, "Original file not found")
    
    return FileResponse(
        input_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"
        }
    )


@app.get("/api/preview/translated/{job_id}")
async def preview_translated_pdf(job_id: str):
    """
    Preview translated PDF in browser
    
    Args:
        job_id: Job identifier
        
    Returns:
        Translated PDF file for inline viewing
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Translation not completed yet")
    
    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(404, "Translated file not found")
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"
        }
    )


# ============================================================================
# BACKGROUND TRANSLATION TASK
# ============================================================================

async def translate_pdf_task(
    job_id: str,
    pdf_path: str,
    source_language: str,
    target_language: str
):
    """
    Background task for PDF translation with enhanced validation
    
    Args:
        job_id: Job identifier
        pdf_path: Path to input PDF
        source_language: Source language
        target_language: Target language
    """
    try:
        update_job(job_id, 5, "Detecting PDF language...")
        
        # Detect actual PDF language
        detected_lang, confidence = detect_pdf_language(pdf_path)
        
        logger.info(f"📊 Language Detection:")
        logger.info(f"   Expected: {source_language}")
        logger.info(f"   Detected: {detected_lang} (confidence: {confidence*100:.0f}%)")
        
        # Validate language match
        validation = validate_language_match(source_language, detected_lang, confidence)
        
        if validation["should_warn"]:
            logger.warning(f"⚠️ {validation['message']}")
        
        # Check if already in target language
        if detected_lang == target_language[:2]:
            fail_job(
                job_id,
                f"⚠️ PDF appears to already be in {target_language}. No translation needed."
            )
            return
        
        update_job(job_id, 10, "Extracting text from PDF...")
        
        # Extract text from PDF with validation
        page_texts, extraction_stats = extract_pdf_text_robust(
            pdf_path,
            source_language,
            validate_language=source_language
        )
        
        total_pages = len(page_texts)
        blank_pages = extraction_stats["blank_pages"]
        non_blank = total_pages - blank_pages
        
        logger.info(f"📄 Extraction complete:")
        logger.info(f"   Total pages: {total_pages}")
        logger.info(f"   Non-blank pages: {non_blank}")
        logger.info(f"   Blank pages: {blank_pages}")
        
        if non_blank == 0:
            fail_job(job_id, "No translatable text found in PDF")
            return
        
        # Show language warning in job message if needed
        if extraction_stats.get("language_warning"):
            warning = extraction_stats["language_warning"]
            update_job(
                job_id,
                15,
                f"⚠️ {warning['message']}. Proceeding with translation..."
            )
        else:
            update_job(job_id, 15, f"Extracted {non_blank} pages, starting translation...")
        
        # Create translator
        update_job(job_id, 20, "Initializing translator...")
        
        translator = HybridTranslatorV2(
            source_language=source_language,
            target_language=target_language,
            mode="general"
        )
        
        # Translate pages
        update_job(job_id, 30, "Translating with Sarvam AI...")
        
        translated_pages = await translator.translate_chunks(page_texts)
        
        update_job(job_id, 80, "Creating translated PDF...")
        
        # Create output PDF
        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
        create_translated_pdf(
            translated_pages,
            output_path,
            target_language
        )
        
        # Complete job
        complete_job(job_id, output_path)
        
        logger.info(f"✅ Translation completed: {job_id}")
        
        # Log statistics
        stats = translator.get_statistics()
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Sarvam AI: {stats['sarvam_used']} chunks")
        logger.info(f"   OpenAI: {stats['openai_used']} chunks")
        logger.info(f"   Blank pages: {stats['blank_pages']}")
        logger.info(f"   Total cost: ₹{stats['total_cost_inr']:.2f}")
        logger.info(f"   Success rate: {stats['success_rate']:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Translation failed: {e}", exc_info=True)
        fail_job(job_id, f"Translation failed: {str(e)}")


# ============================================================================
# VISUALIZATION ENDPOINTS
# ============================================================================

@app.post("/api/visualize")
async def visualize_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    content_type: str = Form("auto"),
    output_format: str = Form("json")
):
    """
    Create visualization from PDF (English only)
    
    Args:
        file: PDF file to visualize
        content_type: Type of content (auto, academic, technical, educational, general)
        output_format: Output format (json or html)
        
    Returns:
        Job ID for tracking visualization progress
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Read file content
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            413,
            f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
        )
    
    # Save temporary file
    temp_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOADS_DIR, f"temp_{temp_id}.pdf")
    
    try:
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Detect language
        detected_lang, confidence = detect_pdf_language(temp_path)
        
        # Check if English
        is_english = detected_lang in ['en', 'eng', 'english']
        if not is_english:
            raise HTTPException(
                400,
                f"Only English PDFs can be visualized. Detected language: {detected_lang}. Please translate to English first."
            )
        
        # Check page count
        import PyPDF2
        with open(temp_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            page_count = len(pdf_reader.pages)
        
        MAX_VIZ_PAGES = 20
        if page_count > MAX_VIZ_PAGES:
            raise HTTPException(
                400,
                f"PDF has {page_count} pages. Visualization is limited to {MAX_VIZ_PAGES} pages."
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        input_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
        with open(input_path, 'wb') as f:
            f.write(content)
        
        # Create job
        create_job(job_id, file.filename, "visualization")
        
        # Start visualization in background
        # FIXED: Call the correct background task function
        background_tasks.add_task(
            visualize_pdf_task,  # ← Changed from visualize_pdf
            job_id,
            input_path,
            content_type,
            output_format
        )
        
        logger.info(f"📊 Visualization job created: {job_id}")
        logger.info(f"   File: {file.filename}")
        logger.info(f"   Pages: {page_count}")
        logger.info(f"   Content type: {content_type}")
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Visualization started"
        }
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


# Background task function (renamed to avoid conflict)
async def visualize_pdf_task(
    job_id: str,
    pdf_path: str,
    content_type: str,
    output_format: str
):
    """
    Background task for PDF visualization using Gemini AI
    
    Args:
        job_id: Job identifier
        pdf_path: Path to PDF file (string path, not UploadFile object)
        content_type: Content type (auto, academic, technical, etc.)
        output_format: Output format (json, html)
    """
    try:
        update_job(job_id, 10, "Initializing visualization service...")
        
        # Import visualization service
        from app.services.pdf_visualizer import get_visualizer_service
        
        visualizer = get_visualizer_service()
        
        update_job(job_id, 20, "Extracting text from PDF...")
        
        # Process PDF with real AI analysis
        # If content_type is 'auto', pass None to let service auto-detect
        content_type_param = None if content_type == "auto" else content_type
        
        update_job(job_id, 40, "Analyzing content with Gemini AI...")
        
        result = visualizer.process_pdf(
            pdf_path=pdf_path,
            content_type=content_type_param,
            max_pages=20,
            output_format=output_format
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Visualization failed")
            fail_job(job_id, error_msg)
            return
        
        update_job(job_id, 80, "Creating visualization output...")
        
        # Save visualization data
        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_visualization.json")
        
        # Save the full result (includes visualization data + metadata)
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Complete job
        complete_job(job_id, output_path)
        
        logger.info(f"✅ Visualization completed: {job_id}")
        logger.info(f"   Content type: {result.get('metadata', {}).get('content_type')}")
        logger.info(f"   Pages processed: {result.get('metadata', {}).get('pages_processed')}")
        
    except Exception as e:
        logger.error(f"❌ Visualization failed: {e}", exc_info=True)
        fail_job(job_id, f"Visualization failed: {str(e)}")



@app.get("/api/visualization/{job_id}")
async def get_visualization(job_id: str, format: str = "json"):
    """
    Get visualization results
    
    Args:
        job_id: Job identifier
        format: Output format (json or html)
        
    Returns:
        Visualization data or HTML
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, f"Visualization not completed yet. Status: {job['status']}")
    
    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(404, "Visualization file not found")
    
    # Read visualization data
    import json
    try:
        with open(output_path, 'r') as f:
            full_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read visualization: {e}")
        raise HTTPException(500, "Failed to read visualization data")
    
    # Extract the actual visualization data (handle nested structure)
    # The file contains: {"success": true, "visualization": {...actual data...}, "metadata": {...}}
    if "visualization" in full_data:
        viz_data = full_data["visualization"]
    else:
        viz_data = full_data
    
    if format == "html":
        # Return enhanced HTML view
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{viz_data.get('title', 'PDF Visualization')}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    line-height: 1.6;
                }}
                .container {{ 
                    max-width: 1000px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 40px; 
                    border-radius: 12px; 
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                h1 {{ 
                    color: #1a202c; 
                    border-bottom: 4px solid #8B5CF6; 
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                    font-size: 2em;
                }}
                h2 {{ 
                    color: #8B5CF6; 
                    margin-top: 35px;
                    margin-bottom: 15px;
                    font-size: 1.5em;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .summary {{ 
                    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                    padding: 20px; 
                    border-left: 5px solid #8B5CF6; 
                    margin: 25px 0; 
                    border-radius: 8px;
                    font-size: 1.05em;
                    line-height: 1.7;
                }}
                .section {{ margin: 30px 0; }}
                .item {{ 
                    background: #f9fafb; 
                    padding: 18px; 
                    margin: 12px 0; 
                    border-left: 4px solid #8B5CF6; 
                    border-radius: 6px;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .item:hover {{
                    transform: translateX(5px);
                    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
                }}
                .item strong {{ 
                    color: #1a202c; 
                    display: block; 
                    margin-bottom: 8px;
                    font-size: 1.1em;
                }}
                .item p {{ color: #4a5568; margin: 5px 0; }}
                .item em {{ color: #718096; font-size: 0.95em; }}
                .concept {{ background: #fef3c7; border-left-color: #f59e0b; }}
                .relationship {{ 
                    background: #dbeafe; 
                    border-left-color: #3b82f6;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-wrap: wrap;
                }}
                .arrow {{ 
                    color: #8B5CF6; 
                    font-weight: bold;
                    padding: 0 5px;
                }}
                .infographic {{ background: #d1fae5; border-left-color: #10b981; }}
                .structure-item {{ 
                    background: white;
                    border: 1px solid #e2e8f0;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 6px;
                }}
                .structure-item.level-1 {{ margin-left: 0; border-left: 4px solid #8B5CF6; }}
                .structure-item.level-2 {{ margin-left: 20px; border-left: 4px solid #a78bfa; }}
                .structure-item.level-3 {{ margin-left: 40px; border-left: 4px solid #c4b5fd; }}
                .structure-item h4 {{ color: #1a202c; margin-bottom: 8px; }}
                .structure-item ul {{ margin-left: 20px; color: #4a5568; }}
                .badge {{ 
                    display: inline-block;
                    background: #8B5CF6;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: 600;
                }}
                .count {{ 
                    background: #e2e8f0;
                    color: #4a5568;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 0.85em;
                    margin-left: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{viz_data.get('title', 'PDF Visualization')}</h1>
                
                <div class="summary">
                    <strong>📄 Summary</strong><br/><br/>
                    {viz_data.get('summary', 'No summary available')}
                </div>
                
                {'<div class="section"><h2>🧠 Main Ideas <span class="count">' + str(len(viz_data.get('main_ideas', []))) + '</span></h2>' + ''.join([f'<div class="item"><strong>{idea.get("idea", "")}</strong><p>{idea.get("explanation", "")}</p>{("<em>💡 Visual: " + idea.get("visual_suggestion", "") + "</em>") if idea.get("visual_suggestion") else ""}</div>' for idea in viz_data.get('main_ideas', [])]) + '</div>' if viz_data.get('main_ideas') else ''}
                
                {'<div class="section"><h2>💡 Key Concepts <span class="count">' + str(len(viz_data.get('key_concepts', []))) + '</span></h2>' + ''.join([f'<div class="item concept"><strong>{c.get("concept", "")}</strong><p>{c.get("definition", "")}</p>{("<em>" + c.get("importance", "") + "</em>") if c.get("importance") else ""}</div>' for c in viz_data.get('key_concepts', [])]) + '</div>' if viz_data.get('key_concepts') else ''}
                
                {'<div class="section"><h2>📊 Key Facts <span class="count">' + str(len(viz_data.get('infographic_elements', []))) + '</span></h2>' + ''.join([f'<div class="item infographic"><strong>{elem.get("type", "fact").title()}</strong><p>{elem.get("content", "")}</p></div>' for elem in viz_data.get('infographic_elements', [])]) + '</div>' if viz_data.get('infographic_elements') else ''}
                
                {'<div class="section"><h2>🔗 Connections <span class="count">' + str(len(viz_data.get('connections', []))) + '</span></h2>' + ''.join([f'<div class="item relationship"><span>{conn.get("item1", "")}</span><span class="arrow">→</span><em>{conn.get("connection", "")}</em><span class="arrow">→</span><span>{conn.get("item2", "")}</span></div>' for conn in viz_data.get('connections', [])]) + '</div>' if viz_data.get('connections') else ''}
                
                {'<div class="section"><h2>🗂️ Document Structure</h2>' + ''.join([f'<div class="structure-item level-{item.get("level", "1")}"><h4>{item.get("title", "")}</h4>' + ('<ul>' + ''.join([f'<li>{point}</li>' for point in item.get("content", [])]) + '</ul>' if item.get("content") else '') + '</div>' for item in viz_data.get('structure', {}).get('hierarchy', [])]) + '</div>' if viz_data.get('structure', {}).get('hierarchy') else ''}
            </div>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    
    else:
        # Return JSON (send the full structure)
        return JSONResponse(content={
            "success": True,
            "visualization": viz_data,
            "metadata": full_data.get("metadata", {
                "job_id": job_id,
                "format": format
            })
        })


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LipiTranslate",
        "version": "2.1.0",
        "features": [
            "Language validation",
            "Blank page detection",
            "Hybrid translation",
            "PDF preview"
        ]
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to LipiTranslate API (Improved)",
        "version": "2.1.0",
        "translator": "Sarvam AI (Primary) + OpenAI (Fallback)",
        "features": [
            "✅ Automatic language detection",
            "✅ Blank page handling",
            "✅ Smart fallback system",
            "✅ PDF preview support"
        ],
        "docs": "/docs"
    }


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )