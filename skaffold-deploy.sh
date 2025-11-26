#!/bin/bash

# Skaffold Deployment Script for Agentic Chatbot
# This script provides easy-to-use commands for deploying with Skaffold

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_build() {
    echo -e "${BLUE}[SKAFFOLD]${NC} $1"
}

# Check if skaffold is installed
if ! command -v skaffold &> /dev/null; then
    print_error "Skaffold is not installed. Please install it first:"
    echo "  macOS: brew install skaffold"
    echo "  Linux: curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64 && sudo install skaffold /usr/local/bin/"
    echo "  Windows: choco install skaffold"
    echo ""
    echo "Or visit: https://skaffold.dev/docs/install/"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No GCP project set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

print_info "Using GCP Project: $PROJECT_ID"

# Update skaffold.yaml with actual project ID
print_info "Updating skaffold.yaml with project ID..."
sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" skaffold.yaml
sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" .skaffold/service.yaml

# Function to show usage
show_usage() {
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev         - Start continuous development mode (watches for changes)"
    echo "  run         - Build and deploy once to Cloud Run"
    echo "  deploy      - Deploy only (skip build)"
    echo "  build       - Build only (skip deploy)"
    echo "  delete      - Delete deployed resources"
    echo "  debug       - Run in debug mode with verbose logging"
    echo "  prod        - Deploy to production (uses prod profile)"
    echo "  staging     - Deploy to staging (uses staging profile)"
    echo ""
    echo "Options:"
    echo "  --tail      - Tail logs after deployment"
    echo "  --no-cache  - Build without cache"
    echo ""
    echo "Examples:"
    echo "  $0 dev              # Start development mode"
    echo "  $0 run --tail       # Deploy once and tail logs"
    echo "  $0 prod             # Deploy to production"
    echo ""
}

# Parse command
COMMAND=${1:-help}
PROFILE="dev"
TAIL_LOGS=false
NO_CACHE=false

# Parse additional arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --tail)
            TAIL_LOGS=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Execute command
case $COMMAND in
    dev)
        print_build "Starting Skaffold in development mode..."
        print_info "Watching for file changes. Press Ctrl+C to stop."
        if [ "$NO_CACHE" = true ]; then
            skaffold dev --profile=dev --no-prune=false --cache-artifacts=false
        else
            skaffold dev --profile=dev --no-prune=false --cache-artifacts=true
        fi
        ;;

    run)
        print_build "Building and deploying to Cloud Run..."
        if [ "$NO_CACHE" = true ]; then
            skaffold run --profile=dev --cache-artifacts=false
        else
            skaffold run --profile=dev --cache-artifacts=true
        fi

        if [ "$TAIL_LOGS" = true ]; then
            print_info "Tailing logs..."
            gcloud run logs tail agentic-chatbot --region=us-central1 --project=$PROJECT_ID
        fi
        ;;

    deploy)
        print_build "Deploying to Cloud Run (skipping build)..."
        skaffold deploy --profile=dev
        ;;

    build)
        print_build "Building container image (skipping deploy)..."
        if [ "$NO_CACHE" = true ]; then
            skaffold build --profile=dev --cache-artifacts=false
        else
            skaffold build --profile=dev --cache-artifacts=true
        fi
        ;;

    delete)
        print_warning "Deleting deployed resources..."
        read -p "Are you sure you want to delete the deployment? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            skaffold delete --profile=dev
            print_info "Resources deleted successfully"
        else
            print_info "Deletion cancelled"
        fi
        ;;

    debug)
        print_build "Running Skaffold in debug mode..."
        skaffold debug --profile=dev --verbosity=debug
        ;;

    prod)
        print_build "Deploying to PRODUCTION environment..."
        read -p "Are you sure you want to deploy to production? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            skaffold run --profile=prod --cache-artifacts=true
            print_info "Production deployment completed!"
        else
            print_info "Production deployment cancelled"
        fi
        ;;

    staging)
        print_build "Deploying to STAGING environment..."
        skaffold run --profile=staging --cache-artifacts=true
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

# Restore original files
if [ -f "skaffold.yaml.bak" ]; then
    rm skaffold.yaml.bak
fi
if [ -f ".skaffold/service.yaml.bak" ]; then
    rm .skaffold/service.yaml.bak
fi

print_info "Done!"
