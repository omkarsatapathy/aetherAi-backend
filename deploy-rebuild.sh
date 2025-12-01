#!/bin/bash

# FULL REBUILD + LOCAL TEST + DEPLOY Script
# Use this when requirements.txt has changed
# This script:
# 1. Builds Docker image locally with updated dependencies
# 2. Runs container locally for testing
# 3. Tests the endpoint
# 4. Pushes to GCR and deploys to Cloud Run

set -e  # Exit on error

PROJECT_ID="effortless-lock-329115"
REGION="us-central1"
SERVICE_NAME="agentic-chatbot"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
LOCAL_PORT=8080
CONTAINER_NAME="agentic-chatbot-local"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📝 Loading API keys from .env file..."
    export $(grep -E "^(GEMINI_API_KEY|OPENAI_API_KEY|GOOGLE_SEARCH_API_KEY|GOOGLE_SEARCH_ENGINE_ID|GOOGLE_MAPS_API_KEY)=" .env | xargs)
else
    echo "⚠️  Warning: .env file not found. API keys will not be configured."
fi

# Step 1: Build Docker image locally
echo ""
echo "🔨 Step 1: Building Docker image locally with updated requirements.txt..."
echo "==========================================================================="
docker build --platform linux/amd64 -f Dockerfile.standalone -t ${IMAGE_NAME}:latest .

# Step 2: Stop any existing container
echo ""
echo "🧹 Step 2: Cleaning up existing containers..."
echo "==========================================================================="
docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

# Step 3: Run container locally
echo ""
echo "🐳 Step 3: Starting container locally on port ${LOCAL_PORT}..."
echo "==========================================================================="

# Check if Firebase service account file exists
FIREBASE_CREDS_MOUNT=""
if [ -f "firebase-service-account.json" ]; then
    echo "✓ Found firebase-service-account.json - mounting into container"
    FIREBASE_CREDS_MOUNT="-v $(pwd)/firebase-service-account.json:/app/firebase-service-account.json -e GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-service-account.json"
else
    echo "⚠️  Warning: firebase-service-account.json not found. Firebase features may not work."
fi

docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${LOCAL_PORT}:8080 \
  $FIREBASE_CREDS_MOUNT \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e GOOGLE_SEARCH_API_KEY="${GOOGLE_SEARCH_API_KEY}" \
  -e GOOGLE_SEARCH_ENGINE_ID="${GOOGLE_SEARCH_ENGINE_ID}" \
  -e GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY}" \
  -e ENVIRONMENT=development \
  -e LOG_LEVEL=INFO \
  ${IMAGE_NAME}:latest

echo "⏳ Waiting for container to start (15 seconds)..."
sleep 15

# Step 4: Test the endpoint
echo ""
echo "🧪 Step 4: Testing local endpoint..."
echo "==========================================================================="

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:${LOCAL_PORT}/health || echo "FAILED")
if [[ $HEALTH_RESPONSE == *"status"* ]]; then
    echo "✅ Health check passed!"
    echo "Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed!"
    echo "Response: $HEALTH_RESPONSE"
    echo ""
    echo "📋 Container logs:"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# Test root endpoint
echo ""
echo "Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:${LOCAL_PORT}/ || echo "FAILED")
if [[ $ROOT_RESPONSE == *"message"* ]]; then
    echo "✅ Root endpoint passed!"
    echo "Response: $ROOT_RESPONSE"
else
    echo "❌ Root endpoint failed!"
    echo "Response: $ROOT_RESPONSE"
fi

# Test chat endpoint with sample payload
echo ""
echo "Testing chat endpoint with sample payload..."
CHAT_PAYLOAD='{
  "session_id": "a1e95d4c-1a0e-4ff5-99b8-b6dfb796d0c3",
  "role": "user",
  "content": "hi tell me the new update !"
}'

echo "Payload:"
echo "$CHAT_PAYLOAD" | jq '.' 2>/dev/null || echo "$CHAT_PAYLOAD"

CHAT_RESPONSE=$(curl -s -X POST http://localhost:${LOCAL_PORT}/api/chat \
  -H "Content-Type: application/json" \
  -d "$CHAT_PAYLOAD" || echo "FAILED")

if [[ $CHAT_RESPONSE != "FAILED" ]]; then
    echo "✅ Chat endpoint responded!"
    echo "Response:"
    echo "$CHAT_RESPONSE" | jq '.' 2>/dev/null || echo "$CHAT_RESPONSE"
else
    echo "❌ Chat endpoint failed!"
    echo "Response: $CHAT_RESPONSE"
fi

# Show container logs
echo ""
echo "📋 Container logs (last 30 lines):"
docker logs --tail 30 ${CONTAINER_NAME}

# Ask user if they want to continue with deployment
echo ""
echo "==========================================================================="
echo "🎯 Local testing complete!"
echo "==========================================================================="
echo ""
echo "Container is running at: http://localhost:${LOCAL_PORT}"
echo ""
echo "You can:"
echo "  - Test more endpoints manually"
echo "  - Check logs with: docker logs ${CONTAINER_NAME}"
echo "  - Stop container with: docker stop ${CONTAINER_NAME}"
echo ""
read -p "Do you want to deploy to Google Cloud Run? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  Deployment cancelled. Container is still running locally."
    echo "To stop it later: docker stop ${CONTAINER_NAME}"
    exit 0
fi

# Step 5: Push to GCR
echo ""
echo "📤 Step 5: Pushing image to Google Container Registry..."
echo "==========================================================================="
docker push ${IMAGE_NAME}:latest

# Step 6: Deploy to Cloud Run
echo ""
echo "☁️  Step 6: Deploying to Cloud Run..."
echo "==========================================================================="

# Build environment variables string
ENV_VARS="ENVIRONMENT=production,LOG_LEVEL=WARNING,LOG_TO_FILE=False,LOG_TO_CONSOLE=True,FASTAPI_HOST=0.0.0.0,FASTAPI_PORT=8080,FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json"

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

# Step 7: Test Cloud Run deployment
echo ""
echo "🧪 Step 7: Testing Cloud Run deployment..."
echo "==========================================================================="

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "Testing health endpoint on Cloud Run..."
CLOUD_HEALTH=$(curl -s ${SERVICE_URL}/health || echo "FAILED")
if [[ $CLOUD_HEALTH == *"status"* ]]; then
    echo "✅ Cloud Run health check passed!"
    echo "Response: $CLOUD_HEALTH"
else
    echo "⚠️  Cloud Run health check response: $CLOUD_HEALTH"
fi

# Test chat endpoint on Cloud Run with sample payload
echo ""
echo "Testing chat endpoint on Cloud Run with sample payload..."
CHAT_PAYLOAD='{
  "session_id": "a1e95d4c-1a0e-4ff5-99b8-b6dfb796d0c3",
  "role": "user",
  "content": "hi tell me the new update !"
}'

echo "Payload:"
echo "$CHAT_PAYLOAD" | jq '.' 2>/dev/null || echo "$CHAT_PAYLOAD"

CLOUD_CHAT_RESPONSE=$(curl -s -X POST ${SERVICE_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d "$CHAT_PAYLOAD" || echo "FAILED")

if [[ $CLOUD_CHAT_RESPONSE != "FAILED" ]]; then
    echo "✅ Cloud Run chat endpoint responded!"
    echo "Response:"
    echo "$CLOUD_CHAT_RESPONSE" | jq '.' 2>/dev/null || echo "$CLOUD_CHAT_RESPONSE"
else
    echo "❌ Cloud Run chat endpoint failed!"
    echo "Response: $CLOUD_CHAT_RESPONSE"
fi

# Cleanup local container
echo ""
echo "🧹 Cleaning up local container..."
docker stop ${CONTAINER_NAME}
docker rm ${CONTAINER_NAME}

# Final summary
echo ""
echo "==========================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "==========================================================================="
echo ""
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📊 Quick test commands:"
echo "  curl ${SERVICE_URL}/health"
echo "  curl ${SERVICE_URL}/"
echo ""
echo "📋 View logs:"
echo "  gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}' --limit 50 --format json"
echo ""
echo "🎉 All done!"
echo ""
