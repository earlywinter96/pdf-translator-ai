"""
FastAPI PDF Translator - Complete Main Application
---------------------------------------------------
Production-ready PDF translation service with job tracking, cleanup, and secure admin dashboard
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
import logging
from typing import Optional
from contextlib import contextmanager
import time

# Relative imports - works when running as: uvicorn app.main:app
from .models.job import (
    create_job, 
    update_job, 
    complete_job, 
    fail_job, 
    get_job, 
    mark_downloaded, 
    start_cleanup_scheduler
)
from .services.translator import TranslatorService
from .services.pdf_reader import extract_text_from_pdf
from .services.chunker import chunk_pages
from .services.pdf_writer import create_pdf_from_text

# Import admin routes (this includes all password management)
from .admin_routes import admin_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="PDF Translator AI",
    description="AI-powered PDF translation for Indian languages with admin dashboard",
    version="2.0.0"
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production
        "https://pdf-translator-ai-xgu2.vercel.app",
        "https://www.pdf-translator-ai-xgu2.vercel.app",
        # Local development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "Content-Type",
        "Content-Length",
        "X-Content-Type-Options"
    ]
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directory Configuration
UPLOADS_DIR = "uploads"
OUTPUTS_DIR = "outputs"

# Language Configuration
LANGUAGE_MAP = {
    "gu": ("guj", "Gujarati"),
    "hi": ("hin", "Hindi"),
    "mr": ("mar", "Marathi"),
}

# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    logger.info("="*70)
    logger.info("🚀 PDF Translator AI Started Successfully")
    logger.info("="*70)
    logger.info(f"📁 Uploads directory: {UPLOADS_DIR}")
    logger.info(f"📁 Outputs directory: {OUTPUTS_DIR}")
    logger.info(f"🔐 Admin dashboard: /admin/dashboard")
    logger.info(f"📚 API docs: /docs")
    
    # Check for admin credentials
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_hash = os.getenv("ADMIN_PASSWORD_HASH")
    
    if not admin_hash:
        logger.warning("⚠️  No ADMIN_PASSWORD_HASH set - using default password")
        logger.warning("⚠️  Run 'python generate_admin_hash.py' to create secure password")
    else:
        logger.info(f"✅ Admin user configured: {admin_user or 'admin'}")
    
    logger.info("="*70)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("="*70)
    logger.info("👋 PDF Translator AI Shutting Down...")
    logger.info("="*70)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class JobTimeoutError(Exception):
    """Raised when job exceeds time limit"""
    pass


class PDFReadError(Exception):
    """Raised when PDF cannot be read properly"""
    pass


# ============================================================================
# BACKGROUND TRANSLATION PROCESSOR
# ============================================================================

def process_translation_job(
    job_id: str,
    pdf_path: str,
    language: str,
    direction: str,
    mode: str
):
    """
    Background task for PDF translation with HARD TIMEOUT (thread-safe)
    
    Args:
        job_id: Unique job identifier
        pdf_path: Path to uploaded PDF
        language: Source/target language code
        direction: Translation direction (to_en/from_en)
        mode: Translation mode (general/government)
    """
    start_time = time.monotonic()
    TIME_LIMIT = 600  # 10 minutes

    def check_timeout():
        """Check if job has exceeded time limit"""
        if time.monotonic() - start_time > TIME_LIMIT:
            raise JobTimeoutError("Job exceeded 10 minute time limit")

    try:
        logger.info(f"🚀 Starting job: {job_id}")
        logger.info(f"   PDF: {pdf_path}")
        logger.info(f"   Language: {language}, Direction: {direction}, Mode: {mode}")

        check_timeout()

        # Step 0: Verify file exists
        if not os.path.exists(pdf_path):
            raise Exception(f"PDF not found: {pdf_path}")

        file_size = os.path.getsize(pdf_path)
        logger.info(f"   Size: {file_size / 1024 / 1024:.2f} MB")

        # Step 1: Extract text from PDF
        update_job(job_id, 10, "Extracting text from PDF...")
        logger.info("📄 Step 1: Text extraction...")

        ocr_lang, lang_name = LANGUAGE_MAP.get(language, ("eng", "English"))
        pages = extract_text_from_pdf(pdf_path, ocr_lang)
        check_timeout()

        total_chars = sum(len(p) for p in pages)
        if total_chars < 50:
            raise PDFReadError("Extracted text too short - PDF may be corrupted or empty")

        logger.info(f"   Extracted {len(pages)} pages, {total_chars} characters")
        update_job(job_id, 30, f"Extracted text from {len(pages)} pages")

        # Step 2: Chunk pages for translation
        logger.info("📝 Step 2: Chunking pages...")
        chunks = chunk_pages(pages)
        check_timeout()

        logger.info(f"   Created {len(chunks)} chunks")
        update_job(job_id, 40, f"Processing {len(chunks)} chunks...")

        # Step 3: Set up translator
        if direction == "to_en":
            source_lang, target_lang = lang_name, "English"
        else:
            source_lang, target_lang = "English", lang_name

        logger.info(f"🌐 Step 3: Translation setup ({source_lang} → {target_lang})")
        
        translator = TranslatorService(
            source_language=source_lang,
            target_language=target_lang,
            mode=mode
        )

        # Step 4: Translate chunks
        logger.info("🔄 Step 4: Translating chunks...")
        translated_chunks = []

        for idx, chunk in enumerate(chunks, start=1):
            check_timeout()

            progress = 40 + int((idx / len(chunks)) * 50)
            update_job(job_id, progress, f"Translating chunk {idx}/{len(chunks)}...")

            translated = translator.translate_chunk(chunk)
            translated_chunks.append(translated)

            logger.info(f"   ✓ Chunk {idx}/{len(chunks)} completed")

        # Step 5: Create output PDF
        logger.info("📄 Step 5: Generating output PDF...")
        update_job(job_id, 90, "Generating translated PDF...")
        
        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")

        create_pdf_from_text(
            translated_chunks,
            output_path,
            "Translated Document"
        )

        # Mark job as complete
        complete_job(job_id)
        logger.info(f"🎉 Job completed successfully: {job_id}")

    except JobTimeoutError as e:
        logger.error(f"⏰ Job timeout: {job_id}")
        fail_job(
            job_id,
            "Processing took too long (10+ minutes). "
            "Try a smaller PDF or contact support."
        )

    except PDFReadError as e:
        logger.error(f"📄 PDF read error in job {job_id}: {str(e)}")
        fail_job(job_id, f"PDF read error: {str(e)}")

    except Exception as e:
        logger.exception(f"❌ Unexpected error in job {job_id}")
        fail_job(job_id, f"Processing error: {str(e)}")


# ============================================================================
# PUBLIC API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "PDF Translator AI with Admin Dashboard",
        "version": "2.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "status": "/api/status/{job_id}",
            "download": "/api/download/{job_id}",
            "admin_dashboard": "/admin/dashboard",
            "api_docs": "/docs"
        },
        "supported_languages": ["Gujarati (gu)", "Hindi (hi)", "Marathi (mr)"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pdf-translator-ai",
        "version": "2.0.0",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "admin_configured": bool(os.getenv("ADMIN_PASSWORD_HASH"))
    }


@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {}


# ============================================================================
# PDF TRANSLATION ENDPOINTS
# ============================================================================

@app.post("/api/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("gu"),
    direction: str = Form("to_en"),
    mode: str = Form("general")
):
    """
    Upload PDF for translation
    
    Args:
        file: PDF file to translate
        language: Language code (gu=Gujarati, hi=Hindi, mr=Marathi)
        direction: Translation direction (to_en or from_en)
        mode: Translation mode (general or government)
    
    Returns:
        JSON with job_id and status message
    """
    logger.info(f"📤 Upload request: {file.filename}")
    logger.info(f"   Language: {language}, Direction: {direction}, Mode: {mode}")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.warning(f"❌ Invalid file type: {file.filename}")
        raise HTTPException(400, "Only PDF files are allowed")
    
    # Validate language
    if language not in LANGUAGE_MAP:
        logger.warning(f"❌ Unsupported language: {language}")
        raise HTTPException(400, f"Unsupported language: {language}. Use: gu, hi, or mr")
    
    # Validate direction
    if direction not in ("to_en", "from_en"):
        logger.warning(f"❌ Invalid direction: {direction}")
        raise HTTPException(400, f"Invalid direction: {direction}. Use: to_en or from_en")
    
    # Validate mode
    if mode not in ("general", "government"):
        logger.warning(f"❌ Invalid mode: {mode}")
        raise HTTPException(400, f"Invalid mode: {mode}. Use: general or government")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    
    # Save uploaded file
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"💾 Saved file: {pdf_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save file: {e}")
        raise HTTPException(500, f"Failed to save file: {str(e)}")
    
    # Create job entry
    create_job(job_id, file.filename)
    
    # Start background translation task
    background_tasks.add_task(
        process_translation_job,
        job_id, pdf_path, language, direction, mode
    )
    
    logger.info(f"✅ Job created: {job_id}")
    
    return {
        "job_id": job_id,
        "message": "Upload successful. Translation started.",
        "status": "processing"
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Get translation job status
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON with status, progress, and message
    """
    logger.info(f"📊 Status request: {job_id}")
    
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    return {
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"]
    }


@app.get("/api/original/{job_id}")
async def get_original_pdf(job_id: str):
    """
    Download original uploaded PDF
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Original PDF file
    """
    logger.info(f"📥 Original download request: {job_id}")
    
    # Check if job exists
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    # Build file path
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    
    # Check if file exists
    if not os.path.exists(original_path):
        logger.error(f"❌ Original file not found: {original_path}")
        if os.path.exists(UPLOADS_DIR):
            files = os.listdir(UPLOADS_DIR)
            logger.info(f"📂 Files in uploads: {files}")
        raise HTTPException(404, "Original file not found")
    
    logger.info(f"✅ Sending original file: {original_path}")
    
    return FileResponse(
        original_path,
        media_type="application/pdf",
        filename=job.get("original_filename", "original.pdf"),
        headers={
            "Content-Disposition": f'attachment; filename="{job.get("original_filename", "original.pdf")}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@app.get("/api/download/{job_id}")
async def download_translated_pdf(job_id: str):
    """
    Download translated PDF
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Translated PDF file
    """
    logger.info(f"📥 Download request: {job_id}")
    
    # Check if job exists
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    logger.info(f"   Job status: {job['status']}, Progress: {job['progress']}%")
    
    # Check if translation completed
    if job["status"] != "completed":
        logger.warning(f"⏳ Job not completed: {job['status']}")
        raise HTTPException(
            400, 
            f"Translation not completed. Status: {job['status']}, Progress: {job['progress']}%"
        )
    
    # Build file path
    output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
    
    # Check if file exists
    if not os.path.exists(output_path):
        logger.error(f"❌ Translated file not found: {output_path}")
        if os.path.exists(OUTPUTS_DIR):
            files = os.listdir(OUTPUTS_DIR)
            logger.info(f"📂 Files in outputs: {files}")
        raise HTTPException(404, "Translated file not found")
    
    logger.info(f"✅ Sending translated file: {output_path}")
    
    # Mark job as downloaded (triggers cleanup after delay)
    mark_downloaded(job_id)
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"translated_{job_id}.pdf",
        headers={
            "Content-Disposition": f'attachment; filename="translated_{job_id}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@app.get("/api/preview/original/{job_id}")
async def preview_original_pdf(job_id: str):
    """
    Preview original PDF (inline in browser)
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        PDF for inline viewing
    """
    logger.info(f"📄 Preview original request: {job_id}")
    
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    
    if not os.path.exists(original_path):
        logger.error(f"❌ Original file not found: {original_path}")
        raise HTTPException(404, "Original file not found")
    
    logger.info(f"✅ Serving original preview: {original_path}")
    
    return FileResponse(
        original_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{job.get("original_filename", "original.pdf")}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cross-Origin-Resource-Policy": "cross-origin",
            "Cross-Origin-Embedder-Policy": "unsafe-none"
        }
    )


@app.get("/api/preview/translated/{job_id}")
async def preview_translated_pdf(job_id: str):
    """
    Preview translated PDF (inline in browser)
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Translated PDF for inline viewing
    """
    logger.info(f"📄 Preview translated request: {job_id}")
    
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    if job["status"] != "completed":
        logger.warning(f"⏳ Job not completed: {job['status']}")
        raise HTTPException(
            400, 
            f"Translation not completed. Status: {job['status']}, Progress: {job['progress']}%"
        )
    
    output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
    
    if not os.path.exists(output_path):
        logger.error(f"❌ Translated file not found: {output_path}")
        raise HTTPException(404, "Translated file not found")
    
    logger.info(f"✅ Serving translated preview: {output_path}")
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="translated_{job_id}.pdf"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cross-Origin-Resource-Policy": "cross-origin",
            "Cross-Origin-Embedder-Policy": "unsafe-none"
        }
    )


# ============================================================================
# TESTING & DIAGNOSTIC ENDPOINTS
# ============================================================================

@app.get("/api/test-tesseract")
async def test_tesseract():
    """
    Check if Tesseract OCR is installed and working
    
    Returns:
        Installation status and version info
    """
    import shutil
    import subprocess
    
    tesseract_path = shutil.which('tesseract')
    
    if tesseract_path:
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "installed": True,
                "path": tesseract_path,
                "version": result.stdout.split('\n')[0]
            }
        except Exception as e:
            return {
                "installed": False,
                "error": str(e)
            }
    else:
        return {
            "installed": False,
            "error": "tesseract not found in PATH"
        }


@app.get("/test-ocr")
async def test_ocr():
    """
    Test OCR setup and verify language availability
    
    Returns:
        OCR status and available languages
    """
    from .services.pdf_reader import test_ocr_setup
    
    success = test_ocr_setup()
    return {
        "ocr_working": success,
        "message": "OCR setup verified" if success else "OCR setup failed. Install Tesseract OCR."
    }


# ============================================================================
# INCLUDE ADMIN ROUTES
# ============================================================================
# This includes all admin endpoints:
# - /admin/dashboard (GET) - View dashboard with usage stats
# - /admin/change-password (POST) - Change admin password
# - /admin/reset-usage (POST) - Reset usage statistics

app.include_router(admin_router)


# ============================================================================
# RUN SERVER (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )