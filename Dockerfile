# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Dependencies layer (only rebuilt when requirements change)
# ============================================
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# This layer is cached and only rebuilt when requirements.txt changes
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Final application layer (rebuilt on every code change)
# ============================================
FROM dependencies AS application

# Copy application code
# These layers are rebuilt when code changes
COPY backend.py .
COPY src/ ./src/
COPY frontend/ ./frontend/

# Create necessary directories with proper permissions
RUN mkdir -p uploads vector_db logs models database/gmail_credentials database/audio && \
    chmod -R 755 uploads vector_db logs models database

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
# Default environment variables for Cloud Run
ENV GEMINI_API_KEY=""
ENV GOOGLE_SEARCH_API_KEY=""
ENV OPENAI_API_KEY=""
ENV LOG_LEVEL="WARNING"
ENV LOG_TO_FILE="False"
ENV LOG_TO_CONSOLE="True"

# Expose the port Cloud Run expects
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application with uvicorn
# Cloud Run sets PORT environment variable, default to 8080
# Use --timeout-keep-alive to handle long-running requests
CMD exec uvicorn backend:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 300
