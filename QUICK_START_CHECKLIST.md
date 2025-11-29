# Quick Start Checklist

## 🚀 Setup Steps (Do These First!)

### ☐ Step 1: Install Dependencies (5 min)
```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend
pip install -r requirements.txt
```
**Look for:** "Successfully installed firebase-admin-6.x.x"

---

### ☐ Step 2: Download Service Account (2 min)
1. Go to: https://console.firebase.google.com/
2. Select: **AetherAi** project
3. Click: ⚙️ → Project Settings → Service Accounts
4. Click: **Generate New Private Key**
5. Save as: `firebase-service-account.json` in backend root

---

### ☐ Step 3: Configure Environment (1 min)
Create `.env` file in backend root:
```env
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

---

### ☐ Step 4: Deploy Firestore Rules (3 min)
1. Go to: Firebase Console → Firestore Database → Rules
2. Copy rules from `FIRESTORE_SCHEMA.md` (lines 66-97)
3. Click **Publish**

---

### ☐ Step 5: Deploy Storage Rules (2 min)
1. Go to: Firebase Console → Storage → Rules
2. Copy rules from `FIRESTORE_SCHEMA.md` (lines 102-114)
3. Click **Publish**

---

### ☐ Step 6: Test Backend (2 min)
```bash
cd /Users/omkarsatapaphy/python_works/aetherAi-backend
uvicorn src.main:app --reload --port 8000
```
**Look for:** "Firebase Admin SDK initialized successfully"

---

### ☐ Step 7: Test Frontend (1 min)
```bash
# New terminal
cd /Users/omkarsatapaphy/python_works/aetherAi-frontend
python -m http.server 3000
```
**Open:** http://localhost:3000

---

### ☐ Step 8: Test Sign-In (2 min)
1. Complete setup wizard (Welcome → Features → Terms)
2. Click "Continue with Google"
3. Sign in with your Google account
4. Should see welcome animation

**Verify in Firebase Console:**
- Firestore → users → {your-id} → (your data)

---

## ✅ Completion Criteria

You're done with setup when all of these are ✅:

- [ ] Backend starts without errors
- [ ] See "Firebase Admin SDK initialized successfully"
- [ ] Frontend loads at localhost:3000
- [ ] Can sign in with Google/Apple/Email
- [ ] User created in Firestore (check console)
- [ ] No console errors

---

## ⚠️ If Something Fails

### Backend won't start
```bash
# Check service account exists
ls firebase-service-account.json

# Check .env exists
cat .env
```

### Sign-in doesn't work
- Check browser console for errors
- Verify firebase-config.js has correct credentials
- Try clearing localStorage: `localStorage.clear()`

### Permission denied in Firestore
- Make sure you deployed the security rules
- Check rules in Firebase Console

---

## 📋 What's Next (After Setup)

### Still Need to Update:
1. Message endpoints (`src/api/routes/messages.py`)
2. Document upload (`src/api/routes/documents.py`)
3. Voice endpoints (`src/api/routes/voice.py`)
4. Frontend API calls (add auth headers)
5. Loading animation

### Reference Files:
- See `IMPLEMENTATION_SUMMARY.md` for detailed instructions
- See `FIREBASE_IMPLEMENTATION.md` for architecture
- See `FIRESTORE_SCHEMA.md` for database structure

---

**Estimated Total Setup Time: 15-20 minutes**

Good luck! 🎉
