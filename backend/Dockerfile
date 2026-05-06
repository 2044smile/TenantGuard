FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    # Playwright Chromium 의존성
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    # Tesseract OCR
    tesseract-ocr tesseract-ocr-kor \
    # OpenCV headless 의존성
    libglib2.0-0 libgl1 \
    # PDF 처리
    poppler-utils \
    # 기타
    wget curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium 설치
RUN playwright install chromium

COPY . .

EXPOSE 8000
