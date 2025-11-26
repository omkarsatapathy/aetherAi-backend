#!/bin/bash

# GCP Deployment Script for Agentic Chatbot Backend
# This script deploys the FastAPI backend to Google Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="agentic-chatbot"
MEMORY="2Gi"
CPU="2"
MAX_INSTANCES="10"
MIN_INSTANCES="0"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID if not set
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
fi

print_info "Using GCP Project: $PROJECT_ID"
print_info "Deploying to region: $REGION"
print_info "Service name: $SERVICE_NAME"

# Confirm deployment
read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Enable required APIs
print_info "Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --project=$PROJECT_ID

# Build and submit to Cloud Build
print_info "Building container image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --project=$PROJECT_ID

# Deploy to Cloud Run
print_info "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory $MEMORY \
    --cpu $CPU \
    --max-instances $MAX_INSTANCES \
    --min-instances $MIN_INSTANCES \
    --timeout 300 \
    --project=$PROJECT_ID

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --format 'value(status.url)')

print_info "====================================="
print_info "Deployment completed successfully!"
print_info "====================================="
print_info "Service URL: $SERVICE_URL"
print_info "Health check: $SERVICE_URL/api/health"
print_info ""
print_info "To view logs, run:"
print_info "gcloud run logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
print_info ""
print_info "To set environment variables, run:"
print_info "gcloud run services update $SERVICE_NAME --region=$REGION --update-env-vars KEY=VALUE --project=$PROJECT_ID"
