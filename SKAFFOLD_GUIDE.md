# Skaffold Deployment Guide for Agentic Chatbot

This guide explains how to use Skaffold for deploying the Agentic Chatbot to Google Cloud Run.

## What is Skaffold?

Skaffold is a command-line tool that facilitates continuous development for cloud-native applications. It automates the build, push, and deploy workflow for your application.

### Benefits of Using Skaffold

- **Fast Iteration**: Automatically rebuilds and redeploys when you change code
- **Smart Caching**: Reuses Docker layers to speed up builds (only rebuilds what changed)
- **Environment Profiles**: Different configurations for dev, staging, and production
- **Integrated with GCP**: Uses Google Cloud Build and Cloud Run seamlessly
- **File Sync**: Hot-reload capability for rapid development

## Prerequisites

### 1. Install Skaffold

**macOS:**
```bash
brew install skaffold
```

**Linux:**
```bash
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
sudo install skaffold /usr/local/bin/
```

**Windows:**
```bash
choco install skaffold
```

Or visit: https://skaffold.dev/docs/install/

### 2. Install and Configure gcloud CLI

```bash
# Install gcloud CLI (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Set your GCP project
gcloud config set project effortless-lock-329115

# Authenticate
gcloud auth login
gcloud auth configure-docker
```

### 3. Enable Required GCP APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com
```

## Quick Start

### Using the Helper Script (Recommended)

We've created a convenient script that wraps Skaffold commands:

```bash
# Make the script executable (first time only)
chmod +x skaffold-deploy.sh

# View available commands
./skaffold-deploy.sh help
```

### Common Commands

#### 1. Development Mode (Continuous Deployment)

Watch for file changes and automatically rebuild/redeploy:

```bash
./skaffold-deploy.sh dev
```

This will:
- Watch your source files for changes
- Automatically rebuild only changed layers
- Redeploy to Cloud Run
- Stream logs to your terminal

Press `Ctrl+C` to stop.

#### 2. Single Deployment

Build and deploy once:

```bash
./skaffold-deploy.sh run
```

With log tailing:
```bash
./skaffold-deploy.sh run --tail
```

#### 3. Build Only (No Deploy)

Just build the container image:

```bash
./skaffold-deploy.sh build
```

#### 4. Deploy Only (Use Existing Image)

Deploy without rebuilding:

```bash
./skaffold-deploy.sh deploy
```

#### 5. Production Deployment

Deploy to production with optimizations:

```bash
./skaffold-deploy.sh prod
```

This uses:
- Google Cloud Build with Kaniko
- Full layer caching
- Optimized build settings

#### 6. Staging Deployment

Deploy to staging environment:

```bash
./skaffold-deploy.sh staging
```

#### 7. Delete Deployment

Remove deployed resources:

```bash
./skaffold-deploy.sh delete
```

#### 8. Debug Mode

Run with verbose logging:

```bash
./skaffold-deploy.sh debug
```

## Using Skaffold Directly

If you prefer to use Skaffold commands directly:

### Development Mode

```bash
skaffold dev --profile=dev
```

### Build and Deploy

```bash
skaffold run --profile=dev
```

### Production Deployment

```bash
skaffold run --profile=prod
```

### Build Only

```bash
skaffold build --profile=dev
```

### Delete Resources

```bash
skaffold delete
```

## Skaffold Profiles

The configuration includes three profiles:

### 1. **dev** Profile

- Uses local Docker builds with push to GCR
- Fast iteration with file sync
- Suitable for development and testing

```bash
./skaffold-deploy.sh dev
# or
skaffold dev --profile=dev
```

### 2. **staging** Profile

- Uses Google Cloud Build
- Medium caching strategy
- For pre-production testing

```bash
./skaffold-deploy.sh staging
# or
skaffold run --profile=staging
```

### 3. **prod** Profile

- Uses Google Cloud Build with Kaniko
- Maximum caching (7-day cache retention)
- Optimized for production deployments
- High-CPU build machines (E2_HIGHCPU_8)

```bash
./skaffold-deploy.sh prod
# or
skaffold run --profile=prod
```

## File Sync for Rapid Development

Skaffold can sync changed files directly to the running container without rebuilding:

**Synced Files:**
- `src/**/*.py` → `/app/src`
- `backend.py` → `/app`

This means when you edit Python files in development mode, Skaffold will:
1. Detect the change
2. Sync the file to the container
3. Restart the application (if configured)

Much faster than a full rebuild!

## Caching Strategy

### Docker Layer Caching

The configuration uses multi-stage Docker builds:

1. **Base Layer**: System dependencies (rarely changes)
2. **Dependencies Layer**: Python packages from `requirements.txt` (changes occasionally)
3. **Application Layer**: Your code (changes frequently)

Only the changed layers are rebuilt.

### Kaniko Cache (Production)

For production builds, Kaniko caches layers in:
```
gcr.io/effortless-lock-329115/agentic-chatbot-cache
```

Cache retention: 7 days (168 hours)

## Configuration Files

### `skaffold.yaml`

Main configuration file with:
- Build settings (Docker, Cloud Build, Kaniko)
- Deploy settings (Cloud Run)
- Profile definitions (dev, staging, prod)

### `.skaffold/service.yaml`

Cloud Run service specification with:
- Resource limits (2 CPU, 2Gi memory)
- Autoscaling (0-10 instances)
- Health checks
- Environment variables

## Comparing Deployment Methods

| Feature | deploy.sh | Skaffold |
|---------|-----------|----------|
| **Build Speed** | Medium | Fast (better caching) |
| **Dev Workflow** | Manual | Automatic (watch mode) |
| **File Sync** | No | Yes |
| **Profiles** | No | Yes (dev/staging/prod) |
| **Complexity** | Simple | More features |
| **Best For** | Production deploys | Development + CI/CD |

## Workflow Examples

### Example 1: Local Development

```bash
# Terminal 1: Start Skaffold in dev mode
./skaffold-deploy.sh dev

# Skaffold is now watching your files
# Edit src/agent/streaming_agent.py
# Skaffold automatically syncs changes and redeploys
# View logs in real-time
```

### Example 2: Testing Before Production

```bash
# Deploy to staging
./skaffold-deploy.sh staging

# Test the staging deployment
# If all good, deploy to production
./skaffold-deploy.sh prod
```

### Example 3: Quick Fix and Deploy

```bash
# Make your code changes
# Build and deploy once
./skaffold-deploy.sh run --tail

# Watch logs to verify the fix
```

## Troubleshooting

### Issue: "Skaffold not found"

**Solution:** Install Skaffold using the installation commands above.

### Issue: "No GCP project set"

**Solution:**
```bash
gcloud config set project effortless-lock-329115
```

### Issue: Build fails with permission errors

**Solution:**
```bash
gcloud auth login
gcloud auth configure-docker
```

### Issue: "API not enabled"

**Solution:**
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

### Issue: Slow builds

**Solutions:**
- Use `--profile=dev` for local builds
- Check Docker layer caching
- Verify Kaniko cache is being used (production profile)

### Issue: File sync not working

**Verify:**
- You're using `skaffold dev` (not `run`)
- Files match the sync patterns in `skaffold.yaml`
- Using the dev profile

## Best Practices

### 1. Development Workflow

```bash
# Use dev mode for active development
./skaffold-deploy.sh dev

# Make changes, test, iterate
# Skaffold handles the rest
```

### 2. Production Deployments

```bash
# Always use the prod profile
./skaffold-deploy.sh prod

# Or for more control:
skaffold run --profile=prod --cache-artifacts=true
```

### 3. Clean Builds

If you need a completely fresh build:

```bash
./skaffold-deploy.sh run --no-cache
```

### 4. Resource Cleanup

Regularly clean up old images:

```bash
# List images
gcloud container images list --repository=gcr.io/effortless-lock-329115

# Delete old images
gcloud container images delete gcr.io/effortless-lock-329115/agentic-chatbot:OLD_TAG
```

## Environment Variables

To add environment variables to your deployment, edit `.skaffold/service.yaml`:

```yaml
env:
  - name: YOUR_ENV_VAR
    value: "your-value"
  - name: ANOTHER_VAR
    value: "another-value"
```

Or use gcloud:

```bash
gcloud run services update agentic-chatbot \
  --region=us-central1 \
  --update-env-vars KEY1=VALUE1,KEY2=VALUE2
```

## Monitoring and Logs

### View Deployment

```bash
gcloud run services describe agentic-chatbot --region=us-central1
```

### View Logs

```bash
gcloud run logs tail agentic-chatbot --region=us-central1
```

### Get Service URL

```bash
gcloud run services describe agentic-chatbot \
  --region=us-central1 \
  --format='value(status.url)'
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy with Skaffold

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: effortless-lock-329115

      - name: Install Skaffold
        run: |
          curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
          sudo install skaffold /usr/local/bin/

      - name: Deploy to Cloud Run
        run: skaffold run --profile=prod
```

## Additional Resources

- [Skaffold Documentation](https://skaffold.dev/docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Kaniko Caching](https://github.com/GoogleContainerTools/kaniko#caching)
- [Docker Layer Caching](https://docs.docker.com/build/cache/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Skaffold logs with `--verbosity=debug`
3. Check Cloud Build logs in GCP Console
4. Review the project README.md

---

**Happy Deploying!** 🚀
