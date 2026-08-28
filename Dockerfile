# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies (FFmpeg, git, libass)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libass-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Create data directories
RUN mkdir -p data/downloads data/audio data/transcripts data/clips data/thumbnails data/jobs data/logs

ENV PYTHONUNBUFFERED=1
ENV BACKEND_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
