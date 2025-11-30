# Gmail OAuth Multi-Tenant Security Design

## Architecture Overview

This document outlines the secure Gmail OAuth implementation for the AetherAI chatbot deployed on Google Cloud Run.

## Security Requirements

1. **User Isolation**: Each user's Gmail credentials must be completely isolated
2. **Persistent Storage**: Credentials must survive container restarts (Cloud Run is stateless)
3. **Encryption**: OAuth tokens must be encrypted at rest
4. **Access Control**: Users can only access their own Gmail data
5. **Audit Trail**: Log all Gmail authentication events

## Implementation Components

### 1. Firestore Schema

```
users/{userId}/
  ├── gmail_credentials/
  │   ├── access_token (encrypted)
  │   ├── refresh_token (encrypted)
  │   ├── token_expiry (timestamp)
  │   ├── scopes (array)
  │   ├── created_at (timestamp)
  │   └── updated_at (timestamp)
```

### 2. Authentication Flow

#### Initial OAuth Flow (User Onboarding)
```
1. User logs into AetherAI → Firebase Auth token obtained
2. Frontend → GET /api/auth/gmail/authorize (with Firebase Auth token)
3. Backend verifies token, gets user UID
4. Backend generates OAuth URL with state={user_uid}
5. User redirects to Google OAuth consent screen
6. User grants permissions
7. Google redirects to /api/auth/gmail/callback?code=xxx&state={user_uid}
8. Backend exchanges code for tokens
9. Backend encrypts tokens and stores in Firestore under users/{user_uid}/gmail_credentials
10. User returns to frontend with success message
```

#### Using Gmail Features
```
1. User asks chatbot about emails
2. Agent calls fetch_gmail_messages with session_id
3. Backend extracts user_id from session (via Firebase Auth middleware)
4. Backend retrieves encrypted credentials from Firestore for that user_id
5. Backend decrypts credentials and uses them to call Gmail API
6. Results returned to user
```

### 3. Token Encryption

OAuth tokens are encrypted using Fernet (symmetric encryption):
- Encryption key stored in environment variable `GMAIL_TOKEN_ENCRYPTION_KEY`
- Each user's tokens encrypted separately
- Decryption happens only in-memory during API calls

### 4. Security Guarantees

- **No shared state**: Each user's credentials stored separately in Firestore
- **Authenticated access**: All Gmail operations require valid Firebase Auth token
- **Encryption at rest**: Tokens encrypted in Firestore
- **Cloud Run safe**: No dependency on ephemeral file system
- **No cross-user access**: User A cannot access User B's credentials

### 5. Frontend Integration

Users authorize Gmail during:
1. Initial setup/onboarding
2. When they first try to use Gmail features (if not authorized)
3. Via account settings page

The frontend handles:
- Detecting when Gmail auth is needed (401/403 errors)
- Opening OAuth popup window
- Handling OAuth callback
- Storing auth status in user profile

### 6. Revocation

Users can revoke Gmail access:
- Frontend calls POST /api/auth/gmail/revoke (with Firebase token)
- Backend deletes credentials from Firestore for that user
- User must re-authorize to use Gmail features again

## Migration from Current System

The current file-based system will be completely replaced:
- Remove dependency on `/tmp/gmail_credentials`
- Remove `credentials.json` from file system (move to Cloud Secret Manager or env var)
- Update all tools to use user-specific Firestore credentials
- Add encryption layer for token storage
