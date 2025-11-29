#!/bin/bash

# LOCAL BUILD + DEPLOY Script (NO Cloud Build charges!)
# This builds Docker image on your local machine and deploys to Cloud Run

set -e  # Exit on error

PROJECT_ID="effortless-lock-329115"
REGION="us-central1"
SERVICE_NAME="agentic-chatbot"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📝 Loading API keys from .env file..."
    # Read API keys from .env
    export $(grep -E "^(GEMINI_API_KEY|OPENAI_API_KEY|GOOGLE_SEARCH_API_KEY|GOOGLE_SEARCH_ENGINE_ID|GOOGLE_MAPS_API_KEY)=" .env | xargs)
else
    echo "⚠️  Warning: .env file not found. API keys will not be configured."
fi

echo "🚀 Building Docker image locally for AMD64/Linux (FREE - no Cloud Build charges)..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Build environment variables string
ENV_VARS="ENVIRONMENT=production,LOG_LEVEL=WARNING,LOG_TO_FILE=False,LOG_TO_CONSOLE=True,FASTAPI_HOST=0.0.0.0,FASTAPI_PORT=8080"

# Add API keys if they exist
if [ ! -z "$GEMINI_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GEMINI_API_KEY=${GEMINI_API_KEY}"
    echo "✓ Added GEMINI_API_KEY"
fi

if [ ! -z "$OPENAI_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},OPENAI_API_KEY=${OPENAI_API_KEY}"
    echo "✓ Added OPENAI_API_KEY"
fi

if [ ! -z "$GOOGLE_SEARCH_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_SEARCH_API_KEY=${GOOGLE_SEARCH_API_KEY}"
    echo "✓ Added GOOGLE_SEARCH_API_KEY"
fi

if [ ! -z "$GOOGLE_SEARCH_ENGINE_ID" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_SEARCH_ENGINE_ID=${GOOGLE_SEARCH_ENGINE_ID}"
    echo "✓ Added GOOGLE_SEARCH_ENGINE_ID"
fi

if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}"
    echo "✓ Added GOOGLE_MAPS_API_KEY"
fi

echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300 \
  --set-env-vars "${ENV_VARS}" \
  --cpu-boost \
  --no-cpu-throttling

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL:"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)'
echo ""
echo "💰 Cost: ₹0 (local build, no Cloud Build charges!)"
echo ""
