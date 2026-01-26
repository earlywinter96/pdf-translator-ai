FROM python:3.11-slim

# Install Tesseract OCR + Poppler + Indian language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create directories
RUN mkdir -p uploads outputs

# Set environment variables for better memory management
ENV PYTHONUNBUFFERED=1
ENV MALLOC_TRIM_THRESHOLD_=100000

EXPOSE 8000

# Start FastAPI with limited workers for free tier
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]