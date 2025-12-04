# Playwright Setup Guide

## Overview

The application now includes **Playwright** as a fallback mechanism for fetching URLs that are protected by anti-bot measures (like Best Buy, Amazon, etc.).

### How it Works

1. **Primary Method**: Standard `requests` + BeautifulSoup (fast, lightweight)
   - Tries 3 times with different user agents
   - ✅ Works for most websites
   - ⚡ Fast (~1 second)

2. **Fallback Method**: Playwright headless browser (robust, handles JavaScript)
   - Only triggered when requests fails (timeout, 403, 429)
   - ✅ Bypasses anti-bot protection
   - ✅ Handles JavaScript-rendered content
   - ⚠️ Slower (~3-5 seconds)
   - ⚠️ Uses more memory (~250-500 MB)

## Local Development Setup

### 1. Install Playwright Package

```bash
pip install playwright
```

### 2. Install Browser Binaries

```bash
playwright install chromium
```

Or install with system dependencies:

```bash
playwright install chromium --with-deps
```

### 3. Test the Installation

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

## Docker/Cloud Run Deployment

### Building the Base Image

The `Dockerfile.base` has been updated to include:
- System dependencies for Chromium
- Playwright Python package
- Chromium browser binaries

**Build the base image:**

```bash
gcloud builds submit --config cloudbuild.base.yaml
```

### What's Included

The base Docker image now includes:

1. **System Dependencies** (Dockerfile.base:13-33):
   - `libnss3`, `libnspr4` - Network Security Services
   - `libatk1.0-0`, `libatk-bridge2.0-0` - Accessibility toolkit
   - `libdrm2`, `libgbm1` - Graphics libraries
   - Other required libraries for Chromium

2. **Playwright Installation** (Dockerfile.base:50):
   - Installs Chromium browser (~150-200 MB)
   - Includes necessary browser dependencies

### Docker Image Size

- **Before Playwright**: ~800 MB
- **After Playwright**: ~1.1 GB (+300 MB)
- ✅ Acceptable for Cloud Run (max 10 GB)

## Configuration

### Browser Arguments (link_executor.py:378-386)

```python
args=[
    '--no-sandbox',              # Required for Docker/Cloud Run
    '--disable-setuid-sandbox',  # Security requirement for containers
    '--disable-dev-shm-usage',   # Use /tmp instead of /dev/shm (limited in containers)
    '--disable-gpu',             # No GPU in containers
    '--no-first-run',            # Skip first-run setup
    '--no-zygote',               # Single-process mode
    '--disable-blink-features=AutomationControlled'  # Hide automation detection
]
```

### Timeouts

- **Standard requests**: 15 seconds per attempt (3 attempts = 45s max)
- **Playwright navigation**: 30 seconds (with fallback to 20s)
- **JavaScript wait**: 2 seconds after page load

## Monitoring & Logs

### Success Logs

```
🎭 Using Playwright fallback for: https://example.com
✅ Playwright successfully fetched URL
```

### Warning Logs

```
Standard fetch failed, trying Playwright fallback
Network idle timeout, trying domcontentloaded for https://example.com
Playwright fallback also failed: Playwright timeout
```

### Error Logs

```
All fetch methods failed
Playwright error: ...
```

## Performance Impact

### Best Case (Standard Request Works)
- **Time**: 1-2 seconds
- **Memory**: ~50 MB

### Fallback Case (Playwright Needed)
- **Time**: 5-10 seconds (includes 3 failed attempts + Playwright)
- **Memory**: ~300-500 MB (browser instance)

### Resource Limits for Cloud Run

Recommended configuration:

```yaml
resources:
  limits:
    memory: 2Gi      # Increased from 1Gi to handle Playwright
    cpu: 2           # 2 vCPUs for better performance
```

## Troubleshooting

### Issue: "Playwright not available"

**Solution**: Install Playwright and browser binaries

```bash
pip install playwright
playwright install chromium
```

### Issue: "Browser executable not found"

**Solution**: Reinstall browser binaries

```bash
playwright install chromium --force
```

### Issue: "Permission denied" in Docker

**Solution**: Ensure `--no-sandbox` flag is set (already configured)

### Issue: High memory usage

**Solution**:
- Browser instances are properly closed after use
- Event loops are cleaned up
- Consider increasing Cloud Run memory limit to 2Gi

## Environment Variables

No additional environment variables needed. Playwright is automatically detected and used as fallback.

## Cost Implications

### Cloud Run Costs

With increased memory (1Gi → 2Gi):
- **Per request**: +$0.0000025 (negligible)
- **Monthly (100k requests)**: +$0.25

### Worth it?

✅ **Yes**, because:
- Only used as fallback (not every request)
- Prevents complete failures on protected sites
- Better user experience
- Still cheaper than proxy services ($20-100/month)

## Testing

Test the fallback mechanism:

```bash
# This should trigger Playwright fallback (Best Buy has anti-bot)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Get me the price of MacBook Pro from https://www.bestbuy.com/...",
    "session_id": "test-session"
  }'
```

Check logs for:
```
🎭 Using Playwright fallback for: https://www.bestbuy.com/...
✅ Playwright successfully fetched URL
```

## Future Improvements

1. **Browser Pool**: Reuse browser instances instead of launching new ones
2. **Selective Fallback**: Maintain a list of known protected domains
3. **Caching**: Cache Playwright results to avoid repeated fetches
4. **Stealth Mode**: Add playwright-stealth plugin for better bot detection evasion

## References

- [Playwright Documentation](https://playwright.dev/python/)
- [Playwright in Docker](https://playwright.dev/python/docs/docker)
- [Cloud Run Resource Limits](https://cloud.google.com/run/docs/configuring/memory-limits)
