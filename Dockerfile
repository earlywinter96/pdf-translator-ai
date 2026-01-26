# Use Python 3.11 slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR with language packs
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    # PDF tools (required for pdf2image)
    poppler-utils \
    # Image processing libraries (required for Pillow)
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # Build tools (required for some Python packages)
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Verify Tesseract installation
RUN tesseract --version && tesseract --list-langs

# Copy requirements and install Python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copy application code
COPY backend/ .

# Create directories
RUN mkdir -p uploads outputs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MALLOC_TRIM_THRESHOLD_=100000

# Tesseract configuration
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
ENV OMP_THREAD_LIMIT=1

# OCR optimization settings
ENV OCR_DPI=150
ENV TESSERACT_TIMEOUT=180
ENV MAX_IMAGE_SIZE=1600

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "300", \
     "--limit-concurrency", "3"]