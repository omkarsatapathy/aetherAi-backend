# Firestore Database Schema

## Collections Structure

### 1. `users` Collection
Stores user profile information.

**Document ID**: Firebase UID
**Path**: `/users/{userId}`

```json
{
  "email": "user@example.com",
  "displayName": "John Doe",
  "photoURL": "https://...",
  "createdAt": Timestamp,
  "lastLogin": Timestamp,
  "updatedAt": Timestamp
}
```

---

### 2. `sessions` Subcollection
Stores chat sessions for each user.

**Path**: `/users/{userId}/sessions/{sessionId}`

```json
{
  "sessionId": "uuid-v4",
  "title": "Chat about Python",
  "hasDocuments": false,
  "vectorDbPath": null,
  "createdAt": Timestamp,
  "updatedAt": Timestamp
}
```

**Indexes Required**:
- `updatedAt` DESC (for listing recent sessions)

---

### 3. `messages` Subcollection
Stores messages within each session.

**Path**: `/users/{userId}/sessions/{sessionId}/messages/{messageId}`

```json
{
  "messageId": "auto-generated-id",
  "role": "user | assistant",
  "content": "Message text content",
  "audioFileRef": "gs://bucket/path/to/file.wav" | null,
  "timestamp": Timestamp
}
```

**Indexes Required**:
- `timestamp` ASC (for chronological ordering)

---

### 4. `documents` Subcollection
Stores metadata for uploaded documents.

**Path**: `/users/{userId}/sessions/{sessionId}/documents/{documentId}`

```json
{
  "documentId": "auto-generated-id",
  "filename": "document.pdf",
  "fileRef": "gs://bucket/users/{userId}/documents/{sessionId}/document.pdf",
  "fileSize": 1024000,
  "mimeType": "application/pdf",
  "uploadedAt": Timestamp
}
```

**Indexes Required**:
- `uploadedAt` ASC

---

## Cloud Storage Structure

### File Organization
```
aetherai-c7218.appspot.com/
└── users/
    └── {userId}/
        ├── audio/
        │   └── {sessionId}/
        │       └── {messageId}.wav
        └── documents/
            └── {sessionId}/
                ├── document1.pdf
                ├── document2.docx
                └── image.png
```

### File Naming Convention
- **Audio files**: `{messageId}.wav`
- **Documents**: Original filename preserved
- **Path format**: `users/{userId}/{type}/{sessionId}/{filename}`

---

## Security Rules

### Firestore Security Rules
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

### Cloud Storage Security Rules
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    // Users directory
    match /users/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

---

## Data Access Patterns

### Common Queries

1. **List user sessions**:
   ```python
   users/{userId}/sessions
   Order by: updatedAt DESC
   Limit: 50
   ```

2. **Get session messages**:
   ```python
   users/{userId}/sessions/{sessionId}/messages
   Order by: timestamp ASC
   ```

3. **Get session documents**:
   ```python
   users/{userId}/sessions/{sessionId}/documents
   Order by: uploadedAt ASC
   ```

---

## Migration from SQLite

### Mapping
- SQLite `sessions` table → Firestore `users/{userId}/sessions/{sessionId}`
- SQLite `messages` table → Firestore `users/{userId}/sessions/{sessionId}/messages/{messageId}`
- SQLite `documents` table → Firestore `users/{userId}/sessions/{sessionId}/documents/{documentId}`

### Key Differences
- User isolation at the root level (`users/{userId}`)
- Hierarchical structure (subcollections)
- No joins required (denormalized)
- Automatic timestamps with `serverTimestamp()`
- File references instead of local paths

---

## Best Practices

1. **Batch Operations**: Use batch writes for related updates
2. **Pagination**: Implement cursor-based pagination for large collections
3. **Caching**: Cache user profile data to reduce reads
4. **Indexes**: Create composite indexes for complex queries
5. **File Cleanup**: Implement Cloud Functions to delete orphaned files
