# GCP Deployment Guide - Agentic Chatbot Backend

This guide walks you through deploying your FastAPI backend to Google Cloud Platform using Cloud Run.

## Overview

**Cloud Run** is GCP's equivalent to AWS Lambda + API Gateway. It's a fully managed platform that:
- Automatically scales from 0 to N instances
- Only charges for actual usage (no idle costs)
- Provides HTTPS endpoints automatically
- Handles load balancing automatically
- Supports custom domains

## Architecture Comparison

| AWS | GCP |
|-----|-----|
| Lambda | Cloud Run |
| API Gateway | Built into Cloud Run |
| ECR | Container Registry / Artifact Registry |
| CloudFormation | Cloud Build (CI/CD) |

## Prerequisites

1. **Install Google Cloud SDK (gcloud CLI)**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with GCP**
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

3. **Set your GCP Project**
   ```bash
   # Create a new project or use existing
   gcloud projects create YOUR-PROJECT-ID --name="Agentic Chatbot"

   # Set as active project
   gcloud config set project YOUR-PROJECT-ID
   ```

4. **Enable Billing**
   - Go to: https://console.cloud.google.com/billing
   - Link a billing account to your project (required for Cloud Run)

## Deployment Methods

### Method 1: Quick Deploy (Recommended for First Time)

Simply run the deployment script:

```bash
./deploy.sh
```

This script will:
- Enable required GCP APIs
- Build your Docker container
- Deploy to Cloud Run
- Configure auto-scaling and resources
- Return your service URL

### Method 2: Manual Step-by-Step

#### Step 1: Enable Required APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 2: Build Container Image
```bash
# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/agentic-chatbot
```

#### Step 3: Deploy to Cloud Run
```bash
gcloud run deploy agentic-chatbot \
  --image gcr.io/YOUR-PROJECT-ID/agentic-chatbot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 300
```

#### Step 4: Get Service URL
```bash
gcloud run services describe agentic-chatbot \
  --region us-central1 \
  --format 'value(status.url)'
```

## Environment Variables

To set environment variables (like API keys from your .env file):

```bash
gcloud run services update agentic-chatbot \
  --region us-central1 \
  --update-env-vars \
    OPENAI_API_KEY="your-key",\
    GOOGLE_API_KEY="your-key",\
    ENVIRONMENT="production"
```

Or use secrets (recommended for sensitive data):

```bash
# Create secret
echo -n "your-api-key" | gcloud secrets create openai-api-key --data-file=-

# Grant Cloud Run access to secret
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Mount secret as environment variable
gcloud run services update agentic-chatbot \
  --region us-central1 \
  --update-secrets OPENAI_API_KEY=openai-api-key:latest
```

## Testing Your Deployment

### Health Check
```bash
curl https://your-service-url.run.app/api/health
```

### Test API Endpoint
```bash
curl -X POST https://your-service-url.run.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, chatbot!",
    "session_id": "test-session"
  }'
```

## Monitoring and Logs

### View Real-time Logs
```bash
gcloud run logs tail agentic-chatbot --region us-central1
```

### View Logs in Console
https://console.cloud.google.com/run

### View Metrics
```bash
gcloud run services describe agentic-chatbot --region us-central1
```

## Cost Optimization

Cloud Run pricing is based on:
- **CPU allocation**: $0.00002400/vCPU-second
- **Memory allocation**: $0.00000250/GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month, 360,000 GiB-seconds, 180,000 vCPU-seconds

Tips to reduce costs:
1. Set `--min-instances 0` (default) to scale to zero when idle
2. Use `--memory 1Gi` if your app doesn't need 2Gi
3. Use `--cpu 1` for lighter workloads
4. Set `--max-instances` to prevent unexpected scaling costs

## Continuous Deployment with Cloud Build

The `cloudbuild.yaml` file enables automated deployments:

1. **Connect to GitHub**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. **Set up trigger** (deploys on git push)
   ```bash
   gcloud builds triggers create github \
     --repo-name=YOUR-REPO \
     --repo-owner=YOUR-GITHUB-USERNAME \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

## Custom Domain (Optional)

1. **Map custom domain**
   ```bash
   gcloud run domain-mappings create \
     --service agentic-chatbot \
     --domain api.yourdomain.com \
     --region us-central1
   ```

2. **Update DNS** with the records shown in the output

## Security Best Practices

1. **Enable authentication** (remove `--allow-unauthenticated` if not needed)
2. **Use Secret Manager** for API keys and credentials
3. **Enable VPC Connector** if accessing private resources
4. **Set up Cloud Armor** for DDoS protection
5. **Use IAM roles** to restrict access

## Updating Your Service

After making code changes:

```bash
# Quick update
./deploy.sh

# Or manually
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/agentic-chatbot
gcloud run deploy agentic-chatbot --image gcr.io/YOUR-PROJECT-ID/agentic-chatbot --region us-central1
```

## Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service agentic-chatbot --region us-central1

# Route traffic to previous revision
gcloud run services update-traffic agentic-chatbot \
  --to-revisions REVISION-NAME=100 \
  --region us-central1
```

## Troubleshooting

### Container fails to start
Check logs:
```bash
gcloud run logs read agentic-chatbot --region us-central1 --limit 50
```

### Port issues
Ensure your app listens on `0.0.0.0:8080` (set via PORT env var)

### Memory issues
Increase memory allocation:
```bash
gcloud run services update agentic-chatbot --memory 4Gi --region us-central1
```

### Timeout issues
Increase timeout (max 3600s):
```bash
gcloud run services update agentic-chatbot --timeout 600 --region us-central1
```

## API Gateway (Advanced)

If you need additional features like rate limiting, API keys, or complex routing, you can add API Gateway in front of Cloud Run:

```bash
# Enable API Gateway
gcloud services enable apigateway.googleapis.com

# Create API config (requires OpenAPI spec)
gcloud api-gateway apis create agentic-chatbot-api

# Deploy gateway
gcloud api-gateway gateways create agentic-chatbot-gateway \
  --api=agentic-chatbot-api \
  --location=us-central1
```

However, for most use cases, Cloud Run's built-in features are sufficient.

## Next Steps

1. Deploy your backend: `./deploy.sh`
2. Set environment variables with your API keys
3. Test your endpoints
4. Deploy your frontend to Cloud Storage + Cloud CDN or Firebase Hosting
5. Set up monitoring and alerts
6. Configure custom domain

## Support

- GCP Documentation: https://cloud.google.com/run/docs
- Pricing Calculator: https://cloud.google.com/products/calculator
- Community: https://stackoverflow.com/questions/tagged/google-cloud-run
