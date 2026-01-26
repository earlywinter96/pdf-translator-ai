FROM python:3.11-slim

# Install system dependencies with Tesseract 5.x for better OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    poppler-utils \
    # Add image processing libraries for better OCR preprocessing
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Verify Tesseract installation
RUN tesseract --version && \
    tesseract --list-langs

WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Copy application code
COPY backend/ .

# Create directories
RUN mkdir -p uploads outputs

# Environment variables for memory optimization
ENV PYTHONUNBUFFERED=1
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV MALLOC_MMAP_THRESHOLD_=131072
ENV MALLOC_TOP_PAD_=131072
ENV PYTHONMALLOC=malloc

# Tesseract configuration for better OCR
ENV OMP_THREAD_LIMIT=1
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

EXPOSE 8000

# Use single worker with limited memory and longer timeout
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "180", \
     "--limit-concurrency", "3", \
     "--timeout-graceful-shutdown", "120"]