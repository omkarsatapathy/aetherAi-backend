# Quick Start - Deployment Commands

## 🚀 Deploy After Code Changes (RECOMMENDED - FREE!)

```bash
./deploy-local.sh
```

**What this does:**
- Builds Docker image on your local machine (no Cloud Build charges!)
- Pushes to Google Container Registry
- Deploys to Cloud Run
- **Cost: ₹0 (FREE!)**
- **Time: 1-2 minutes**

---

## 📦 After Adding/Updating Python Packages

When you modify `requirements.txt`:

### Step 1: Rebuild base image
```bash
docker build -f Dockerfile.base -t gcr.io/effortless-lock-329115/agentic-chatbot-base:latest .
docker push gcr.io/effortless-lock-329115/agentic-chatbot-base:latest
```

### Step 2: Deploy application
```bash
./deploy-local.sh
```

---

## 📝 Full Documentation

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions, troubleshooting, and advanced options.

---

## 🌐 Your Service

- **URL:** https://agentic-chatbot-589407533049.us-central1.run.app
- **Health Check:** https://agentic-chatbot-589407533049.us-central1.run.app/health

---

## 💡 Why Use deploy-local.sh?

| Method | Cost | Speed | Notes |
|--------|------|-------|-------|
| `./deploy-local.sh` | **₹0** | 1-2 min | ✅ Recommended |
| Cloud Build | ₹15-30 | 3-5 min | Only use if local build fails |

**Save money!** Use `./deploy-local.sh` for all your deployments.
