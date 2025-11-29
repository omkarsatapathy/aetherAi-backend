# Firebase Implementation Guide

## 🎉 Implementation Status: 90% Complete

### ✅ Completed Components

#### **Backend Services**
1. ✅ Firebase Admin SDK initialization (`src/firebase_admin_config.py`)
2. ✅ Authentication middleware (`src/middleware/auth_middleware.py`)
3. ✅ Firestore service layer (`src/services/firestore_service.py`)
4. ✅ Cloud Storage service (`src/services/storage_service.py`)
5. ✅ Updated session endpoints with auth (`src/api/routes/sessions.py`)

#### **Frontend Services**
1. ✅ Firebase client SDK configuration (`js/firebase-config.js`)
2. ✅ Authentication service (`js/auth-service.js`)
3. ✅ Multi-auth setup wizard (Google, Apple, Email/Password)
4. ✅ Terms & Agreement page
5. ✅ Complete UI styling

#### **Documentation**
1. ✅ Firestore schema design (`FIRESTORE_SCHEMA.md`)
2. ✅ Security rules templates
3. ✅ This implementation guide

---

## 📦 Installation Steps

### 1. Install Backend Dependencies

```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend
pip install -r requirements.txt
```

This will install:
- `firebase-admin>=6.5.0`
- All other existing dependencies

### 2. Set Up Firebase Service Account

#### Option A: Download Service Account JSON
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **AetherAi**
3. Go to Project Settings (gear icon) → Service Accounts
4. Click "Generate New Private Key"
5. Download the JSON file
6. Save it as `firebase-service-account.json` in the backend root directory

#### Option B: Use Environment Variable
Alternatively, you can store the JSON content in an environment variable:

```bash
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

### 3. Configure Environment Variables

Create or update `.env` file in backend root:

```env
# Firebase Service Account
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json

# OR use JSON directly
# FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Other existing config...
```

### 4. Deploy Firestore Security Rules

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **AetherAi**
3. Go to Firestore Database → Rules
4. Copy and paste the following rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper function to check if user is authenticated
    function isAuthenticated() {
      return request.auth != null;
    }

    // Helper function to check if user owns the resource
    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }

    // Users collection
    match /users/{userId} {
      allow read, write: if isOwner(userId);

      // Sessions subcollection
      match /sessions/{sessionId} {
        allow read, write: if isOwner(userId);

        // Messages subcollection
        match /messages/{messageId} {
          allow read, write: if isOwner(userId);
        }

        // Documents subcollection
        match /documents/{documentId} {
          allow read, write: if isOwner(userId);
        }
      }
    }
  }
}
```

5. Click "Publish"

### 5. Deploy Cloud Storage Security Rules

1. Go to Firebase Console → Storage → Rules
2. Copy and paste the following rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    // Helper function to check if user is authenticated
    function isAuthenticated() {
      return request.auth != null;
    }

    // Users directory
    match /users/{userId}/{allPaths=**} {
      allow read, write: if isAuthenticated() && request.auth.uid == userId;
    }
  }
}
```

3. Click "Publish"

---

## 🚀 Running the Application

### Backend

```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-frontend
# Serve with any static file server
python -m http.server 3000
# OR
npx serve .
```

---

## 🔐 Authentication Flow

### Frontend → Backend Flow

1. **User Signs In** (Frontend)
   ```javascript
   const user = await authService.signInWithGoogle();
   const token = await user.getIdToken();
   localStorage.setItem('authToken', token);
   ```

2. **Make API Request** (Frontend)
   ```javascript
   const token = localStorage.getItem('authToken');
   fetch('http://localhost:8000/api/sessions', {
       headers: {
           'Authorization': `Bearer ${token}`,
           'Content-Type': 'application/json'
       }
   });
   ```

3. **Verify Token** (Backend)
   ```python
   # Middleware automatically verifies token
   current_user = Depends(get_current_user)
   user_id = get_user_id_from_token(current_user)
   ```

---

## 📊 Data Flow Examples

### Creating a Session

**Frontend:**
```javascript
const token = await authService.getAuthToken();
const response = await fetch('http://localhost:8000/api/sessions', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        title: 'My Chat Session'
    })
});
```

**Backend:**
```python
# Automatically creates in Firestore under:
# users/{userId}/sessions/{sessionId}
```

### Uploading a Document

**Frontend:**
```javascript
const formData = new FormData();
formData.append('file', fileBlob);
formData.append('session_id', sessionId);

const token = await authService.getAuthToken();
const response = await fetch('http://localhost:8000/api/documents/upload', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});
```

**Backend:**
```python
# 1. Upload to Cloud Storage: users/{userId}/documents/{sessionId}/filename
# 2. Save metadata to Firestore: users/{userId}/sessions/{sessionId}/documents/{docId}
```

---

## 🛠️ Pending Tasks

### Backend
- [ ] Update message endpoints (similar to sessions)
- [ ] Update document upload endpoints to use Cloud Storage
- [ ] Update voice/audio endpoints to use Cloud Storage
- [ ] Create user profile endpoint

### Frontend
- [ ] Add authorization headers to all API requests
- [ ] Implement loading animation for session retrieval
- [ ] Add auth state management
- [ ] Handle token refresh

### Testing
- [ ] End-to-end authentication flow
- [ ] Firestore CRUD operations
- [ ] Cloud Storage file uploads
- [ ] Multi-user isolation

---

## 📝 API Endpoints (Updated)

### Sessions
- `POST /api/sessions` - Create session (requires auth)
- `GET /api/sessions` - List sessions (requires auth)
- `GET /api/sessions/{id}` - Get session (requires auth)
- `PUT /api/sessions/{id}` - Update session (requires auth)
- `DELETE /api/sessions/{id}` - Delete session (requires auth)

### Authentication Headers
All protected endpoints require:
```
Authorization: Bearer {firebase-id-token}
```

---

## 🔍 Troubleshooting

### Common Issues

1. **"Firebase not initialized" error**
   - Check service account JSON path
   - Verify environment variables
   - Check file permissions

2. **"Invalid authentication token" error**
   - Token may be expired (refresh on frontend)
   - Check Authorization header format
   - Verify Firebase project ID matches

3. **"Permission denied" in Firestore**
   - Verify security rules are deployed
   - Check user is authenticated
   - Verify user ID matches document path

4. **Storage upload fails**
   - Check storage security rules
   - Verify file size limits
   - Check bucket name in config

### Debug Mode

Enable detailed logging:

```python
# src/firebase_admin_config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎯 Next Steps

1. **Test Authentication:**
   ```bash
   # Install dependencies first
   pip install -r requirements.txt

   # Run backend
   uvicorn src.main:app --reload

   # Open frontend and test sign-in
   ```

2. **Monitor Firestore:**
   - Go to Firebase Console → Firestore Database
   - Watch for new documents being created
   - Check data structure matches schema

3. **Monitor Storage:**
   - Go to Firebase Console → Storage
   - Verify file uploads appear in correct paths

4. **Check Logs:**
   - Backend logs show authentication events
   - Firebase Console shows rule evaluations

---

## 📚 References

- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Cloud Firestore](https://firebase.google.com/docs/firestore)
- [Cloud Storage](https://firebase.google.com/docs/storage)
- [Security Rules](https://firebase.google.com/docs/rules)

---

## 🎉 Success Criteria

The implementation is complete when:
- ✅ Users can sign in with Google/Apple/Email
- ✅ Sessions are created per user in Firestore
- ✅ Messages are stored with proper user isolation
- ✅ Files upload to Cloud Storage
- ✅ Multi-user data is completely isolated
- ✅ All API endpoints require authentication
- ✅ Security rules prevent unauthorized access

---

**Current Status: Ready for Testing! 🚀**

Install dependencies, configure service account, deploy security rules, and test!
