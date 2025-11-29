#!/bin/bash

# Local build and deploy script
# Builds Docker image locally and deploys to Cloud Run
# This is much faster than Cloud Build for iterative development

set -e  # Exit on error

# Configuration
PROJECT_ID="effortless-lock-329115"
SERVICE_NAME="agentic-chatbot"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "========================================="
echo "Local Build & Deploy to Cloud Run"
echo "========================================="
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Step 1: Configure Docker for GCR
echo "Step 1: Configuring Docker authentication..."
gcloud auth configure-docker --quiet

# Step 2: Build Docker image locally with all CPU cores
echo ""
echo "Step 2: Building Docker image locally (using all CPU cores)..."
echo "Image: ${IMAGE_NAME}:latest"
# Remove existing image if present
docker rmi ${IMAGE_NAME}:latest 2>/dev/null || true
# Use BuildKit for parallel builds and all available CPU cores
DOCKER_BUILDKIT=1 docker build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  -t ${IMAGE_NAME}:latest \
  .

# Step 3: Push to GCR
echo ""
echo "Step 3: Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Step 4: Deploy to Cloud Run
echo ""
echo "Step 4: Deploying to Cloud Run..."
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
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=WARNING,LOG_TO_FILE=False,LOG_TO_CONSOLE=True,FASTAPI_HOST=0.0.0.0,FASTAPI_PORT=8080" \
  --cpu-boost \
  --no-cpu-throttling

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Service URL:"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)'
echo ""
