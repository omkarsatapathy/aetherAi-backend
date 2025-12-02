# Anthropic Claude on Vertex AI Setup Guide

This guide will help you set up Anthropic Claude models via Google Cloud Vertex AI for your chatbot.

## Prerequisites

1. A Google Cloud account with billing enabled
2. Your Google Cloud subscription for Anthropic (which you mentioned you have)

## Step 1: Install Required Packages

First, install the Anthropic Vertex AI SDK:

```bash
pip install 'anthropic[vertex]'
```

Also install Google Cloud SDK if you don't have it:

```bash
# For macOS (using Homebrew)
brew install --cask google-cloud-sdk

# OR download from: https://cloud.google.com/sdk/docs/install
```

## Step 2: Find Your Google Cloud Project ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. At the top of the page, click on the project dropdown
3. Your Project ID will be shown next to the project name
4. Copy this Project ID (it looks like: `my-project-12345`)

## Step 3: Enable Vertex AI API

1. Go to [Vertex AI API page](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
2. Make sure your correct project is selected
3. Click "Enable" if not already enabled

## Step 4: Authenticate with Google Cloud

Open your terminal and run:

```bash
# Authenticate with your Google account
gcloud auth application-default login
```

This will:
1. Open a browser window
2. Ask you to log in with your Google account
3. Ask for permission to access your Google Cloud resources
4. Save credentials to your local machine

Alternative authentication (if you have a service account):

```bash
# If you have a service account JSON key file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

## Step 5: Configure Environment Variables

Update your `.env` file with your Google Cloud Project ID:

```env
# Google Cloud Platform (for Anthropic Vertex AI)
GCP_PROJECT_ID=your-actual-project-id-here
GCP_LOCATION=us-east5
```

Replace `your-actual-project-id-here` with the Project ID you copied in Step 2.

**Available Regions:**
- `us-east5` (recommended for Claude Sonnet 4)
- `europe-west1`
- `global`

## Step 6: Verify Setup

Run this command to check if authentication is working:

```bash
gcloud auth application-default print-access-token
```

If this prints an access token, you're authenticated correctly!

## Step 7: Test the Integration

You can test if Anthropic Vertex AI is available by checking the provider status in your application.

## Available Models

Your application now supports these Claude models via Vertex AI:

### Recommended (Pinned Versions):
- `claude-sonnet-4@20250514` - Claude Sonnet 4 (Latest, recommended)
- `claude-3-5-sonnet@20241022` - Claude 3.5 Sonnet
- `claude-3-opus@20240229` - Claude 3 Opus (Most powerful)
- `claude-3-sonnet@20240229` - Claude 3 Sonnet
- `claude-3-haiku@20240307` - Claude 3 Haiku (Fastest)

### Unpinned Versions (not recommended for production):
- `claude-sonnet-4`
- `claude-3-5-sonnet`
- `claude-3-opus`

## Usage in Your Application

Once configured, you can use Anthropic via Vertex AI in your code:

```python
from src.agent.google_adk.model_providers import get_adk_model

# Use Claude Sonnet 4 via Vertex AI
model = get_adk_model("anthropic-vertex/claude-sonnet-4@20250514")

# Or use the shorter unpinned version
model = get_adk_model("anthropic-vertex/claude-sonnet-4")
```

## Model Selection Priority

Your application will automatically select models in this order:
1. **Google Gemini** (if GEMINI_API_KEY is set)
2. **OpenAI** (if OPENAI_API_KEY is set)
3. **Anthropic Vertex AI** (if GCP_PROJECT_ID is set and authenticated)
4. **Anthropic Direct API** (if ANTHROPIC_API_KEY is set)
5. Local models (Ollama, LlamaCpp)

## Troubleshooting

### "Not configured" error

**Cause:** GCP_PROJECT_ID is not set or Google Cloud authentication is missing

**Solution:**
1. Make sure `GCP_PROJECT_ID` is set in `.env`
2. Run `gcloud auth application-default login`
3. Restart your application

### "Permission denied" error

**Cause:** Your Google account doesn't have access to Vertex AI

**Solution:**
1. Make sure Vertex AI API is enabled in your project
2. Make sure your account has the required IAM roles:
   - `Vertex AI User` or
   - `AI Platform Admin`

To add roles:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:YOUR_EMAIL" \
    --role="roles/aiplatform.user"
```

### "Model not found" error

**Cause:** The Claude model may not be available in your selected region

**Solution:**
Try changing `GCP_LOCATION` in `.env` to:
- `us-east5` (primary region for Claude Sonnet 4)
- `europe-west1`
- `global`

### Authentication expired

**Cause:** Google Cloud credentials expire after some time

**Solution:**
Re-run the authentication command:
```bash
gcloud auth application-default login
```

## Pricing

Claude models on Vertex AI are billed through your Google Cloud account. Check:
- [Anthropic Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- Your Google Cloud billing console

## Benefits of Vertex AI vs Direct Anthropic API

✅ **Unified billing** - All costs through Google Cloud
✅ **Better GCP integration** - Works seamlessly with other GCP services
✅ **Enterprise features** - VPC, audit logs, IAM controls
✅ **No separate API key needed** - Uses Google Cloud authentication

## Need Help?

- [Anthropic Vertex AI Documentation](https://docs.anthropic.com/en/api/claude-on-vertex-ai)
- [Google Cloud Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Anthropic Vertex SDK](https://github.com/anthropics/anthropic-sdk-python)
