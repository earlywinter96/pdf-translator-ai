from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
import os
import shutil
import traceback
from app.config import TRANSLATION_MODES
from app.utils.cleanup import schedule_file_cleanup


from app.services.pdf_reader import extract_text_from_pdf
from app.services.chunker import chunk_pages
from app.services.translator import TranslatorService
from app.services.pdf_writer import create_pdf_from_text
from app.utils.file_utils import generate_job_id, ensure_dir
from app.config import (
    UPLOAD_DIR,
    OUTPUT_DIR,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE
)
from app.models.job import (
    create_job,
    update_job,
    complete_job,
    fail_job,
    JOB_STORE
)

router = APIRouter(prefix="/api")


# -------------------------------
# TRANSLATE PDF
# -------------------------------
@router.post("/translate")
async def translate_pdf(
    file: UploadFile = File(...),
    language: str = Form(DEFAULT_LANGUAGE),
    direction: str = Form("to_en"),
    mode: str = Form("general"),
):
    # -------------------------
    # Validate inputs
    # -------------------------
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language",
        )

    if mode not in TRANSLATION_MODES:
        raise HTTPException(
            status_code=400,
            detail="Invalid translation mode",
        )

    if direction not in ("to_en", "from_en"):
        raise HTTPException(
            status_code=400,
            detail="Invalid translation direction",
        )

    lang_config = SUPPORTED_LANGUAGES[language]

    # -------------------------
    # Determine languages
    # -------------------------
    if direction == "to_en":
        source_language = lang_config["label"]
        target_language = "English"
        ocr_lang = lang_config["ocr"]
    else:
        source_language = "English"
        target_language = lang_config["label"]
        ocr_lang = None  # OCR not needed for English PDFs

    # -------------------------
    # Create job
    # -------------------------
    job_id = generate_job_id()
    create_job(job_id)

    ensure_dir(UPLOAD_DIR)
    ensure_dir(OUTPUT_DIR)

    input_pdf_path = os.path.join(UPLOAD_DIR, f"{job_id}.pdf")
    output_pdf_path = os.path.join(
        OUTPUT_DIR,
        f"{job_id}_translated.pdf",
    )

    try:
        # -------------------------
        # 1️⃣ Save PDF
        # -------------------------
        update_job(job_id, 5, "Saving PDF")
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ Schedule cleanup AFTER file exists
        schedule_file_cleanup(input_pdf_path)

        # -------------------------
        # 2️⃣ Extract text (OCR if needed)
        # -------------------------
        update_job(job_id, 15, "Extracting text")
        pages = extract_text_from_pdf(
            input_pdf_path,
            ocr_lang=ocr_lang,
        )

        # -------------------------
        # 3️⃣ Chunk text
        # -------------------------
        update_job(job_id, 30, "Chunking text")
        chunks = chunk_pages(pages)

        # -------------------------
        # 4️⃣ Translate chunks
        # -------------------------
        translator = TranslatorService(
            source_language=source_language,
            target_language=target_language,
            mode=mode,
        )

        translated_chunks = []
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks, start=1):
            translated_chunks.append(
                translator.translate_chunk(chunk)
            )

            progress = 30 + int((idx / total_chunks) * 50)
            update_job(
                job_id,
                progress,
                f"Translating chunk {idx}/{total_chunks}",
            )

        # -------------------------
        # 5️⃣ Generate PDF
        # -------------------------
        update_job(job_id, 90, "Generating translated PDF")
        create_pdf_from_text(
            translated_chunks,
            output_pdf_path,
        )

        # ✅ Schedule output cleanup
        schedule_file_cleanup(output_pdf_path)

        # -------------------------
        # 6️⃣ Complete job
        # -------------------------
        update_job(job_id, 100, "Completed")
        complete_job(job_id)

        return {
            "job_id": job_id,
            "message": "Translation completed successfully",
        }

    except Exception as e:
        traceback.print_exc()  # 🔥 critical for debugging
        fail_job(job_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# -------------------------------
# DOWNLOAD TRANSLATED PDF
# -------------------------------
@router.get("/download/{job_id}")
def download_translated_pdf(job_id: str):
    file_path = os.path.join(
        OUTPUT_DIR,
        f"{job_id}_translated.pdf"
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{job_id}_translated.pdf"
    )


# -------------------------------
# JOB STATUS (PROGRESS)
# -------------------------------
@router.get("/status/{job_id}")
def get_job_status(job_id: str):
    job = JOB_STORE.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job

@router.get("/original/{job_id}")
def download_original_pdf(job_id: str):
    file_path = os.path.join(
        UPLOAD_DIR,
        f"{job_id}.pdf"
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Original PDF not found"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{job_id}_original.pdf"
    )

