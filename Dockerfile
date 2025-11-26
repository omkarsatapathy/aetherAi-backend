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

# Create necessary directories
RUN mkdir -p uploads vector_db logs models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port Cloud Run expects
EXPOSE 8080

# Run the application with uvicorn
# Cloud Run sets PORT environment variable, default to 8080
CMD exec uvicorn backend:app --host 0.0.0.0 --port ${PORT} --workers 1
