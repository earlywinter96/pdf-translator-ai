"""
FastAPI PDF Translator - Complete Main Application
---------------------------------------------------
Production-ready PDF translation service with job tracking and cleanup
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
import logging
from typing import Optional

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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Translator API",
    description="Translate PDFs between English and Indian languages",
    version="1.0.0"
)

# CORS Configuration - Enhanced for file downloads
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production: ["https://yourdomain.com"]
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

# Directory Configuration
UPLOADS_DIR = "uploads"
OUTPUTS_DIR = "outputs"

# Language Configuration
LANGUAGE_MAP = {
    "gu": ("guj", "Gujarati"),
    "hi": ("hin", "Hindi"),
    "mr": ("mar", "Marathi"),
}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    logger.info("✅ PDF Translator API started successfully")
    logger.info(f"📁 Uploads directory: {UPLOADS_DIR}")
    logger.info(f"📁 Outputs directory: {OUTPUTS_DIR}")


def process_translation_job(
    job_id: str,
    pdf_path: str,
    language: str,
    direction: str,
    mode: str
):
    """
    Background task for PDF translation
    
    Args:
        job_id: Unique job identifier
        pdf_path: Path to uploaded PDF
        language: Source/target language code (gu, hi, mr)
        direction: Translation direction (to_en or from_en)
        mode: Translation mode (general or government)
    """
    try:
        logger.info(f"🚀 Starting translation job: {job_id}")
        
        # Step 1: Extract text from PDF
        update_job(job_id, 10, "Extracting text from PDF...")
        
        ocr_lang, lang_name = LANGUAGE_MAP.get(language, ("eng", "English"))
        pages = extract_text_from_pdf(pdf_path, ocr_lang)
        
        logger.info(f"📄 Extracted text from {len(pages)} pages")
        update_job(job_id, 30, f"Text extracted from {len(pages)} pages")
        
        # Step 2: Chunk pages for translation
        chunks = chunk_pages(pages)
        logger.info(f"🔪 Split into {len(chunks)} chunks")
        update_job(job_id, 40, f"Processing {len(chunks)} text chunks...")
        
        # Step 3: Determine source and target languages
        if direction == "to_en":
            source_lang = lang_name
            target_lang = "English"
        else:
            source_lang = "English"
            target_lang = lang_name
        
        logger.info(f"🌐 Translating {source_lang} → {target_lang}")
        
        # Step 4: Initialize translator
        translator = TranslatorService(
            source_language=source_lang,
            target_language=target_lang,
            mode=mode
        )
        
        # Step 5: Translate chunks
        translated_chunks = []
        total_chunks = len(chunks)
        
        for idx, chunk in enumerate(chunks, start=1):
            progress = 40 + int((idx / total_chunks) * 50)
            update_job(job_id, progress, f"Translating chunk {idx}/{total_chunks}...")
            
            translated_text = translator.translate_chunk(chunk)
            translated_chunks.append(translated_text)
            
            logger.info(f"✅ Translated chunk {idx}/{total_chunks}")
        
        # Step 6: Create output PDF
        update_job(job_id, 90, "Creating translated PDF...")
        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_translated.pdf")
        create_pdf_from_text(translated_chunks, output_path, "Translated Document")
        
        logger.info(f"📝 Created translated PDF: {output_path}")
        
        # Step 7: Mark job as completed
        complete_job(job_id)
        logger.info(f"✅ Translation completed: {job_id}")
        
    except Exception as e:
        logger.error(f"❌ Translation failed for {job_id}: {str(e)}")
        fail_job(job_id, str(e))


# ================================
# API ENDPOINTS
# ================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PDF Translator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pdf-translator-api"
    }


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
        language: Language code (gu, hi, mr)
        direction: Translation direction (to_en, from_en)
        mode: Translation mode (general, government)
    
    Returns:
        JSON with job_id and message
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
        raise HTTPException(400, f"Unsupported language: {language}")
    
    # Validate direction
    if direction not in ("to_en", "from_en"):
        logger.warning(f"❌ Invalid direction: {direction}")
        raise HTTPException(400, f"Invalid direction: {direction}")
    
    # Validate mode
    if mode not in ("general", "government"):
        logger.warning(f"❌ Invalid mode: {mode}")
        raise HTTPException(400, f"Invalid mode: {mode}")
    
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
        "message": "Upload successful. Translation started."
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
        # Debug: List directory contents
        if os.path.exists(UPLOADS_DIR):
            files = os.listdir(UPLOADS_DIR)
            logger.info(f"📂 Files in uploads: {files}")
        raise HTTPException(404, f"Original file not found")
    
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
        # Debug: List directory contents
        if os.path.exists(OUTPUTS_DIR):
            files = os.listdir(OUTPUTS_DIR)
            logger.info(f"📂 Files in outputs: {files}")
        raise HTTPException(404, f"Translated file not found")
    
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
    """Preview original PDF (inline in browser)"""
    logger.info(f"📄 Preview original request: {job_id}")
    
    job = get_job(job_id)
    if not job:
        logger.warning(f"❌ Job not found: {job_id}")
        raise HTTPException(404, f"Job not found: {job_id}")
    
    original_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    
    if not os.path.exists(original_path):
        logger.error(f"❌ Original file not found: {original_path}")
        raise HTTPException(404, f"Original file not found")
    
    logger.info(f"✅ Serving original preview: {original_path}")
    
    return FileResponse(
        original_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{job.get("original_filename", "original.pdf")}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@app.get("/api/preview/translated/{job_id}")
async def preview_translated_pdf(job_id: str):
    """Preview translated PDF (inline in browser)"""
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
        raise HTTPException(404, f"Translated file not found")
    
    logger.info(f"✅ Serving translated preview: {output_path}")
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="translated_{job_id}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )










# ================================
# RUN SERVER (for development)
# ================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )