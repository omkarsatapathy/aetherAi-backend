# Gmail OAuth Setup Guide for AetherAI

This guide explains how to set up Gmail OAuth authentication for your AetherAI deployment on Google Cloud Run.

## Prerequisites

1. Google Cloud Project with Cloud Run enabled
2. Firebase project configured for authentication
3. Google OAuth credentials for Gmail API

## Step 1: Create Google OAuth Credentials

### 1.1 Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** > **Library**
4. Search for "Gmail API"
5. Click **Enable**

### 1.2 Create OAuth Client ID

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Configure:
   - **Name**: `AetherAI Gmail Integration`
   - **Authorized JavaScript origins**:
     - `https://your-cloud-run-url.run.app`
     - `http://localhost:8080` (for local testing)
   - **Authorized redirect URIs**:
     - `https://your-cloud-run-url.run.app/api/auth/gmail/callback`
     - `http://localhost:8080/api/auth/gmail/callback` (for local testing)
5. Click **Create**
6. **Download the JSON file** (you'll need this)

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (or Internal if using Google Workspace)
3. Fill in required information:
   - App name: `AetherAI`
   - User support email: Your email
   - Developer contact email: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
5. Add test users (if in testing mode)
6. Save and continue

## Step 2: Configure Environment Variables

### 2.1 Set Up OAuth Client Configuration

You have two options:

#### Option A: Environment Variable (Recommended for Cloud Run)

```bash
# Get the JSON content from your downloaded credentials file
export GOOGLE_OAUTH_CLIENT_CONFIG='{"web":{"client_id":"your-client-id.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["https://your-app.run.app/api/auth/gmail/callback"]}}'
```

#### Option B: Secret Manager (Best for Production)

1. Upload credentials to Google Secret Manager:
```bash
gcloud secrets create gmail-oauth-config --data-file=credentials.json
```

2. Grant Cloud Run access to the secret:
```bash
gcloud secrets add-iam-policy-binding gmail-oauth-config \
    --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

3. Mount the secret in your Cloud Run service (see deployment section below)

### 2.2 Set Up Token Encryption Key

Generate a secure encryption key for storing OAuth tokens in Firestore:

```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set as environment variable:
```bash
export GMAIL_TOKEN_ENCRYPTION_KEY='your-generated-key-here'
```

## Step 3: Update Cloud Run Deployment

### 3.1 Update `.env` file (for local testing)

```env
# Gmail OAuth Configuration
GOOGLE_OAUTH_CLIENT_CONFIG='{"web":{...}}'  # From Step 2.1
GMAIL_TOKEN_ENCRYPTION_KEY='your-encryption-key'  # From Step 2.2

# Other existing configurations...
```

### 3.2 Deploy to Cloud Run

Update your `deploy.sh` or deploy manually with environment variables:

```bash
#!/bin/bash

# Deploy to Cloud Run with Gmail configuration
gcloud run deploy aetherAI-backend \
    --image gcr.io/YOUR-PROJECT-ID/aetherAI-backend \
    --platform managed \
    --region YOUR-REGION \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_OAUTH_CLIENT_CONFIG=${GOOGLE_OAUTH_CLIENT_CONFIG}" \
    --set-env-vars="GMAIL_TOKEN_ENCRYPTION_KEY=${GMAIL_TOKEN_ENCRYPTION_KEY}" \
    --set-env-vars="GMAIL_DEFAULT_MAX_RESULTS=15" \
    --set-env-vars="GMAIL_MAX_RESULTS_LIMIT=50" \
    --set-env-vars="GMAIL_BODY_MAX_LENGTH=5000"
```

Or using Secret Manager:

```bash
gcloud run deploy aetherAI-backend \
    --image gcr.io/YOUR-PROJECT-ID/aetherAI-backend \
    --platform managed \
    --region YOUR-REGION \
    --allow-unauthenticated \
    --set-secrets="GOOGLE_OAUTH_CLIENT_CONFIG=gmail-oauth-config:latest" \
    --set-env-vars="GMAIL_TOKEN_ENCRYPTION_KEY=${GMAIL_TOKEN_ENCRYPTION_KEY}"
```

## Step 4: Firestore Setup

The application will automatically create the necessary Firestore collections:

```
users/
  {userId}/
    gmail_credentials/
      oauth/
        - access_token (encrypted)
        - refresh_token (encrypted)
        - token_uri
        - client_id
        - client_secret (encrypted)
        - scopes
        - expiry
        - created_at
        - updated_at
```

### Firestore Security Rules

Add these rules to protect user Gmail credentials:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Gmail credentials - users can only access their own
    match /users/{userId}/gmail_credentials/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## Step 5: Frontend Integration

The frontend already has Gmail integration code in `/js/modules/gmail.js`.

### 5.1 Add Gmail Settings to UI

Add a settings page or section where users can manage their Gmail connection:

```html
<!-- In your settings page -->
<div id="settings-container">
    <!-- Gmail settings will be inserted here by gmail.js -->
</div>
```

### 5.2 Initialize Gmail Module

In your main JavaScript file:

```javascript
import { initializeGmailUI } from './modules/gmail.js';

// After user authentication
document.addEventListener('DOMContentLoaded', () => {
    initializeGmailUI();
});
```

## Step 6: User Flow

### Authorization Flow

1. User logs into AetherAI with Firebase Auth
2. User navigates to Settings or Account page
3. User clicks "Connect Gmail"
4. Popup window opens with Google OAuth consent screen
5. User grants permissions
6. Credentials are encrypted and stored in Firestore
7. User can now use Gmail features in the chatbot

### Using Gmail Features

1. User asks chatbot: "Check my recent emails"
2. Agent calls `fetch_gmail_messages` tool
3. Tool retrieves user-specific encrypted credentials from Firestore
4. Tool decrypts credentials and calls Gmail API
5. Results returned to user

## Step 7: Testing

### Local Testing

1. Set environment variables in `.env`
2. Run backend locally:
```bash
python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8080
```

3. Open frontend and test Gmail authorization

### Production Testing

1. Deploy to Cloud Run
2. Log in with Firebase Auth
3. Go to Settings > Gmail Integration
4. Click "Connect Gmail"
5. Complete OAuth flow
6. Test by asking: "Show me my latest emails"

## Troubleshooting

### Issue: "OAuth client configuration not found"

**Solution**: Verify `GOOGLE_OAUTH_CLIENT_CONFIG` environment variable is set correctly.

### Issue: "Invalid redirect URI"

**Solution**: Make sure the redirect URI in your OAuth credentials matches exactly:
- `https://your-app.run.app/api/auth/gmail/callback`

### Issue: "Failed to decrypt credentials"

**Solution**: Ensure `GMAIL_TOKEN_ENCRYPTION_KEY` hasn't changed. If it has, users need to re-authorize.

### Issue: "User A can see User B's emails"

**Solution**: This should NOT happen. Check that:
1. Firebase Auth middleware is working
2. `user_id` is correctly extracted from token
3. Firestore rules are properly set

## Security Best Practices

1. **Never log OAuth tokens** - They grant access to user Gmail
2. **Use HTTPS only** - HTTP is not allowed for OAuth
3. **Rotate encryption keys periodically** - Users will need to re-authorize
4. **Monitor Firestore access** - Watch for unusual patterns
5. **Limit OAuth scopes** - Only request `gmail.readonly`
6. **Validate all user input** - Never trust client-side data
7. **Use Secret Manager** - Don't hardcode credentials in code

## Monitoring

### Logs to Watch

```bash
# Check Gmail auth events
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Gmail.*auth'" --limit 50

# Check for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR AND textPayload=~'Gmail'" --limit 50
```

### Metrics to Track

- Gmail API quota usage
- OAuth token refresh rate
- Authentication failures
- User authorization rate

## Cost Considerations

- **Gmail API**: Free up to 1 billion quota units/day
- **Firestore**: Free tier includes 1GB storage, 50K reads/day
- **Secret Manager**: $0.06 per secret version per month
- **Cloud Run**: Pay per request (existing costs)

## Support

For issues:
1. Check logs in Cloud Console
2. Verify Firestore security rules
3. Test OAuth flow manually
4. Review this guide
5. Contact your development team

---

**Last Updated**: 2025-11-30
**Version**: 1.0.0
