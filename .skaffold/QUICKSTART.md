# Skaffold Quick Start

## Installation

```bash
# macOS
brew install skaffold

# Linux
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
sudo install skaffold /usr/local/bin/

# Windows
choco install skaffold
```

## First Time Setup

```bash
# Set your GCP project
gcloud config set project effortless-lock-329115

# Authenticate
gcloud auth login
gcloud auth configure-docker

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

## Quick Commands

### Using Helper Script (Easiest)

```bash
# Development mode (auto-rebuild on changes)
./skaffold-deploy.sh dev

# Single deployment
./skaffold-deploy.sh run

# Production deployment
./skaffold-deploy.sh prod

# View all commands
./skaffold-deploy.sh help
```

### Direct Skaffold Commands

```bash
# Development mode
skaffold dev --profile=dev

# Build and deploy once
skaffold run --profile=dev

# Production deployment
skaffold run --profile=prod

# Build only (no deploy)
skaffold build --profile=dev

# Deploy only (use existing image)
skaffold deploy

# Delete deployment
skaffold delete
```

## Profiles

- **dev**: Fast local builds, file sync enabled
- **staging**: Cloud Build, medium caching
- **prod**: Cloud Build with Kaniko, maximum caching

## What Gets Synced?

In dev mode, these files sync without rebuilding:
- `src/**/*.py` → `/app/src`
- `backend.py` → `/app/backend.py`

## Troubleshooting

```bash
# Check Skaffold version
skaffold version

# Run with debug logging
skaffold dev --verbosity=debug

# Clear cache
rm -rf ~/.skaffold/cache

# Verify gcloud auth
gcloud auth list
```

## Next Steps

Read the full guide: [SKAFFOLD_GUIDE.md](../SKAFFOLD_GUIDE.md)
