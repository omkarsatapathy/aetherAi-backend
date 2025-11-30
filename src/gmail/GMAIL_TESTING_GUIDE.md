# Gmail OAuth Testing Guide

This guide walks you through testing the secure multi-tenant Gmail OAuth implementation step-by-step.

## Prerequisites

Before testing, ensure you have:

1. ✅ Google OAuth credentials created (see `GMAIL_SETUP_GUIDE.md`)
2. ✅ Firebase project configured
3. ✅ Firestore database initialized
4. ✅ Required environment variables set

## Testing Phases

### Phase 1: Local Backend Testing (Without Frontend)

#### Step 1.1: Install Dependencies

```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend

# Install the new cryptography dependency
pip install cryptography

# Or reinstall all requirements
pip install -r requirements.txt
```

#### Step 1.2: Set Up Environment Variables

Create or update your `.env` file:

```bash
# Gmail OAuth Configuration
GOOGLE_OAUTH_CLIENT_CONFIG='{"web":{"client_id":"YOUR-CLIENT-ID.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR-CLIENT-SECRET","redirect_uris":["http://localhost:8080/api/auth/gmail/callback"]}}'

# Generate encryption key (run this command once):
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GMAIL_TOKEN_ENCRYPTION_KEY='your-generated-fernet-key-here'

# Gmail settings
GMAIL_DEFAULT_MAX_RESULTS=15
GMAIL_MAX_RESULTS_LIMIT=50
GMAIL_BODY_MAX_LENGTH=5000

# Your existing Firebase and other configs...
```

#### Step 1.3: Start Backend Server

```bash
# Make sure you're in the backend directory
cd /Users/omkarsatapaphy/python_works/aetherAi-backend

# Start the server
python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8080 --reload
```

Check for any startup errors. You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

#### Step 1.4: Test Health Endpoint

```bash
# Test that the server is running
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"ok"}
```

#### Step 1.5: Test Gmail Routes (Manual OAuth Flow)

**IMPORTANT**: For this test, you need a valid Firebase Auth token. Here's how to get one:

##### Option A: Get Token from Frontend

1. Open your frontend in browser
2. Log in with Firebase
3. Open browser console (F12)
4. Run:
```javascript
firebase.auth().currentUser.getIdToken().then(token => console.log(token));
```
5. Copy the token

##### Option B: Create Test User and Get Token

```python
# Create a test script: test_auth.py
import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin
cred = credentials.Certificate('path/to/your/firebase-credentials.json')
firebase_admin.initialize_app(cred)

# Create or get test user
try:
    user = auth.create_user(
        email='testuser@example.com',
        password='testpassword123'
    )
    print(f"Created user: {user.uid}")
except auth.EmailAlreadyExistsError:
    user = auth.get_user_by_email('testuser@example.com')
    print(f"User exists: {user.uid}")

# Create custom token
custom_token = auth.create_custom_token(user.uid)
print(f"\nCustom Token: {custom_token.decode()}")
print("\nUse this to sign in on frontend and get ID token")
```

Now test the endpoints:

```bash
# Replace YOUR_FIREBASE_TOKEN with actual token
TOKEN="YOUR_FIREBASE_TOKEN"

# 1. Check Gmail auth status (should be not authenticated initially)
curl -X GET "http://localhost:8080/api/auth/gmail/status" \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {"authenticated":false,"user_id":"user-uid-here","message":"Not authenticated","metadata":null}

# 2. Start OAuth flow (this will redirect to Google)
# Open this URL in your browser (replace TOKEN):
http://localhost:8080/api/auth/gmail/authorize
# Add the Authorization header via browser extension or use curl:

curl -L "http://localhost:8080/api/auth/gmail/authorize" \
  -H "Authorization: Bearer $TOKEN"

# This will redirect you to Google's consent screen
# After authorizing, you'll be redirected back to /api/auth/gmail/callback
# If successful, you'll see a success page

# 3. Check status again (should now be authenticated)
curl -X GET "http://localhost:8080/api/auth/gmail/status" \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {"authenticated":true,"user_id":"user-uid-here","message":"Authenticated","metadata":{...}}
```

#### Step 1.6: Verify Firestore Storage

Check that credentials were saved:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Firestore Database**
4. Look for collection structure:
   ```
   users/
     {your-user-id}/
       gmail_credentials/
         oauth/
           - access_token (encrypted - should be gibberish)
           - refresh_token (encrypted)
           - created_at
           - updated_at
   ```

The tokens should be encrypted (look like random characters).

### Phase 2: Test Gmail Tool Functionality

#### Step 2.1: Test Gmail Tool Directly

Create a test script:

```python
# test_gmail_tool.py
import asyncio
from src.gmail.tool import fetch_gmail_messages
from src.gmail.auth_manager import GmailAuthManager

async def test_gmail():
    # Replace with your Firebase user ID
    user_id = "YOUR_USER_ID_FROM_FIREBASE"

    # Check auth status
    auth_manager = GmailAuthManager()
    is_auth = auth_manager.is_authenticated(user_id)
    print(f"User authenticated: {is_auth}")

    if is_auth:
        # Fetch emails
        result = fetch_gmail_messages(
            user_id=user_id,
            max_results=5,
            query=""
        )
        print(f"\nGmail result:\n{result}")
    else:
        print("User not authenticated. Complete OAuth flow first.")

# Run the test
asyncio.run(test_gmail())
```

Run it:
```bash
python test_gmail_tool.py
```

Expected output:
```json
{
  "messages": [
    {
      "id": "...",
      "subject": "...",
      "from": "...",
      "date": "...",
      "snippet": "...",
      "body": "..."
    }
  ],
  "count": 5,
  "query": ""
}
```

### Phase 3: Full Integration Testing with Frontend

#### Step 3.1: Update Frontend Configuration

Ensure your frontend's `config.js` points to your backend:

```javascript
// js/config.js
export const API_BASE_URL = 'http://localhost:8080'; // For local testing
// export const API_BASE_URL = 'https://your-app.run.app'; // For production
```

#### Step 3.2: Add Gmail UI to Frontend

If you haven't already, add a settings page with Gmail integration:

```html
<!-- In your index.html or settings.html -->
<div id="settings-page" style="display:none;">
    <h2>Settings</h2>
    <div id="settings-container"></div>
</div>
```

Update your main.js to initialize Gmail UI:

```javascript
// In your main.js or app.js
import { initializeGmailUI } from './modules/gmail.js';

// After user logs in
firebase.auth().onAuthStateChanged((user) => {
    if (user) {
        // User is signed in
        initializeGmailUI();
    }
});
```

#### Step 3.3: Test Frontend OAuth Flow

1. **Start backend** (if not already running):
   ```bash
   python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8080 --reload
   ```

2. **Start frontend**:
   ```bash
   cd /Users/omkarsatapaphy/python_works/aetherAi-frontend
   python3 -m http.server 3000
   # Or use your preferred method
   ```

3. **Open browser**: `http://localhost:3000`

4. **Log in** with Firebase Auth

5. **Navigate to Settings** (or wherever you added Gmail UI)

6. **Test Gmail Connection**:
   - Click "Connect Gmail" button
   - Popup window should open
   - Google OAuth consent screen appears
   - Select your Google account
   - Grant permissions
   - Popup closes automatically
   - Status updates to "✅ Gmail connected"

7. **Test Gmail Features in Chat**:
   - Go to chat interface
   - Ask: "Show me my latest emails"
   - Agent should fetch and display your emails

#### Step 3.4: Test Multi-User Isolation

This is CRITICAL for security:

1. **Create two test users**:
   - User A: `testa@example.com`
   - User B: `testb@example.com`

2. **Test with User A**:
   - Log in as User A
   - Connect Gmail (use Google account A)
   - Ask: "Show my emails"
   - Note the emails shown

3. **Test with User B**:
   - Log out
   - Log in as User B
   - Connect Gmail (use Google account B - different from A)
   - Ask: "Show my emails"
   - **VERIFY**: Should see User B's emails, NOT User A's

4. **Security Test**:
   - While logged in as User B
   - Open browser console
   - Try to manually call API with User A's ID (this SHOULD fail):
   ```javascript
   // This should NOT work due to middleware
   fetch('http://localhost:8080/api/auth/gmail/status', {
       headers: {
           'Authorization': 'Bearer ' + userBToken, // User B's token
           'X-User-ID': 'userA-uid' // Trying to access User A's data
       }
   });
   ```
   - Should get 401 or return User B's status, not User A's

### Phase 4: Cloud Run Deployment Testing

#### Step 4.1: Deploy to Cloud Run

```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend

# Build and deploy
gcloud run deploy aetherai-backend \
    --source . \
    --platform managed \
    --region YOUR-REGION \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_OAUTH_CLIENT_CONFIG=${GOOGLE_OAUTH_CLIENT_CONFIG}" \
    --set-env-vars="GMAIL_TOKEN_ENCRYPTION_KEY=${GMAIL_TOKEN_ENCRYPTION_KEY}"
```

#### Step 4.2: Update OAuth Redirect URI

Important! Update your Google OAuth credentials:

1. Go to Google Cloud Console > APIs & Services > Credentials
2. Edit your OAuth client
3. Add redirect URI:
   ```
   https://your-actual-cloud-run-url.run.app/api/auth/gmail/callback
   ```
4. Save

#### Step 4.3: Test Production Flow

1. Update frontend `API_BASE_URL` to Cloud Run URL
2. Deploy frontend (Firebase Hosting or your method)
3. Repeat Phase 3 tests on production

### Phase 5: Error Testing

Test error scenarios to ensure proper handling:

#### Test 5.1: Not Authenticated Error

```bash
# Try to fetch emails without OAuth
curl -X POST "http://localhost:8080/api/chat/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show my emails",
    "session_id": "test-session",
    "conversation_history": []
  }'
```

Expected: Agent should return message asking user to authorize Gmail.

#### Test 5.2: Token Expiry

1. Connect Gmail
2. Wait for token to expire (or manually expire it in Firestore)
3. Ask for emails
4. Should automatically refresh token and work

#### Test 5.3: Revoke Access

```bash
# Revoke access
curl -X POST "http://localhost:8080/api/auth/gmail/revoke" \
  -H "Authorization: Bearer $TOKEN"

# Try to fetch emails (should fail gracefully)
# Ask chatbot for emails
# Should prompt to re-authorize
```

### Phase 6: Performance Testing

#### Test 6.1: Concurrent Users

Simulate multiple users accessing Gmail simultaneously:

```python
# concurrent_test.py
import asyncio
import aiohttp

async def test_user(session, user_token, user_id):
    async with session.get(
        'http://localhost:8080/api/auth/gmail/status',
        headers={'Authorization': f'Bearer {user_token}'}
    ) as resp:
        result = await resp.json()
        print(f"User {user_id}: {result}")

async def main():
    # Create tokens for multiple test users
    users = [
        ('token1', 'user1'),
        ('token2', 'user2'),
        ('token3', 'user3'),
    ]

    async with aiohttp.ClientSession() as session:
        tasks = [test_user(session, token, uid) for token, uid in users]
        await asyncio.gather(*tasks)

asyncio.run(main())
```

## Troubleshooting Common Issues

### Issue: "GOOGLE_OAUTH_CLIENT_CONFIG not found"

**Fix**: Verify environment variable is set:
```bash
echo $GOOGLE_OAUTH_CLIENT_CONFIG
```

### Issue: "Invalid redirect URI"

**Fix**: Ensure redirect URI in OAuth credentials exactly matches:
- Local: `http://localhost:8080/api/auth/gmail/callback`
- Production: `https://your-app.run.app/api/auth/gmail/callback`

### Issue: "Failed to decrypt credentials"

**Fix**:
1. Check `GMAIL_TOKEN_ENCRYPTION_KEY` is set and hasn't changed
2. If changed, users need to re-authorize Gmail

### Issue: "401 Unauthorized" on all endpoints

**Fix**:
1. Verify Firebase Auth token is valid
2. Check middleware is correctly extracting user_id
3. Ensure Authorization header format: `Bearer YOUR_TOKEN`

### Issue: Popup blocked

**Fix**: User needs to allow popups for your domain in browser settings.

## Success Criteria

Your implementation is working correctly if:

- ✅ Users can authorize Gmail via OAuth popup
- ✅ Credentials are encrypted and stored in Firestore
- ✅ Users can fetch their emails via chatbot
- ✅ Each user only sees their own emails (multi-tenant isolation)
- ✅ Tokens automatically refresh when expired
- ✅ Users can revoke access
- ✅ No errors in Cloud Run logs
- ✅ Works for multiple concurrent users

## Monitoring After Deployment

```bash
# Watch logs
gcloud logging tail --project=YOUR-PROJECT

# Filter Gmail-related logs
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Gmail'" --limit 50

# Check errors
gcloud logging read "severity>=ERROR AND textPayload=~'Gmail'" --limit 20
```

## Next Steps

Once testing is complete:

1. ✅ Remove test users
2. ✅ Enable OAuth verification (if required by Google)
3. ✅ Set up monitoring alerts
4. ✅ Document for users
5. ✅ Train support team on Gmail feature

---

**Need Help?**
- Check logs: `gcloud logging tail`
- Verify Firestore data
- Review `GMAIL_SETUP_GUIDE.md`
- Check Firebase Auth is working
