#!/bin/bash

# Script to set environment variables in Cloud Run from your local .env file
# This reads your .env file and sets them in Cloud Run

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SERVICE_NAME="agentic-chatbot"
REGION="us-central1"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create a .env file with your environment variables"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

print_info "Project ID: $PROJECT_ID"
print_info "Service: $SERVICE_NAME"
print_info "Region: $REGION"

# Parse .env file and build env vars string
print_info "Reading environment variables from .env file..."

ENV_VARS=""
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^#.*$ ]] && continue

    # Remove quotes from value if present
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

    # Skip if value is empty
    [[ -z "$value" ]] && continue

    # Add to ENV_VARS string
    if [ -z "$ENV_VARS" ]; then
        ENV_VARS="${key}=${value}"
    else
        ENV_VARS="${ENV_VARS},${key}=${value}"
    fi

    print_info "Found: $key"
done < .env

if [ -z "$ENV_VARS" ]; then
    print_error "No valid environment variables found in .env file"
    exit 1
fi

print_warning "This will update environment variables for $SERVICE_NAME"
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Cancelled"
    exit 0
fi

# Update Cloud Run service with environment variables
print_info "Updating Cloud Run service with environment variables..."
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --update-env-vars="$ENV_VARS" \
    --project=$PROJECT_ID

print_info "Environment variables updated successfully!"
print_info ""
print_info "To verify, run:"
print_info "gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].env)'"
