# Use Python 3.11 slim for smaller size
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR with language packs
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    # PDF tools
    poppler-utils \
    # Image processing libraries
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Verify Tesseract installation
RUN tesseract --version && tesseract --list-langs

WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip cache purge

# Copy application code
COPY backend/ .

# Create directories
RUN mkdir -p uploads outputs

# CRITICAL: Environment variables for OCR optimization
ENV PYTHONUNBUFFERED=1
ENV MALLOC_TRIM_THRESHOLD_=100000

# Tesseract OCR configuration
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
ENV OMP_THREAD_LIMIT=1

# OCR SPEED OPTIMIZATIONS
ENV OCR_DPI=150
ENV TESSERACT_TIMEOUT=180
ENV MAX_IMAGE_SIZE=1600

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

EXPOSE 8000

# Run with increased timeout for OCR operations
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "300", \
     "--limit-concurrency", "3", \
     "--timeout-graceful-shutdown", "120"]
