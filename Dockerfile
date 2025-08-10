FROM python:3.10-slim

LABEL maintainer="Invoice Reader Team"

# Install system dependencies required for PDF processing and OCR.
# - tesseract-ocr and language data for Spanish (spa), Galician (glg) and English (eng)
# - ghostscript and poppler for Camelot/tabula
# - libgl1 and libglib2.0-0 for PyMuPDF and pillow image handling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-spa \
        tesseract-ocr-glg \
        ghostscript \
        libglib2.0-0 \
        libgl1 \
        poppler-utils \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specification and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app app

EXPOSE 8000

# Define default command to run the API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
