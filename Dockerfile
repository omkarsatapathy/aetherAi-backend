# Application Dockerfile using pre-built base image
# This only copies code, making deployments VERY fast (1-2 minutes)
# Similar to AWS SAM's approach - dependencies in layers, code updated separately

# Use the pre-built base image with all dependencies
# When requirements.txt changes, rebuild base image with: gcloud builds submit --config cloudbuild.base.yaml
FROM gcr.io/effortless-lock-329115/agentic-chatbot-base:latest

# Set working directory (already set in base, but explicit is good)
WORKDIR /app

# Copy application code
# Only these layers are rebuilt on code changes (FAST!)
COPY backend.py .
COPY src/ ./src/

# Set environment variables for Cloud Run (override base if needed)
ENV GEMINI_API_KEY=""
ENV GOOGLE_SEARCH_API_KEY=""
ENV OPENAI_API_KEY=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application with uvicorn
# Cloud Run sets PORT environment variable, default to 8080
CMD exec uvicorn backend:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 300