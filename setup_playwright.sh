#!/bin/bash
# Setup script for Playwright installation

set -e  # Exit on error

echo "🎭 Playwright Setup Script"
echo "=========================="
echo ""

# Check if running in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not running in a virtual environment"
    echo "   Recommend activating your virtual environment first"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if playwright is already installed
if python -c "import playwright" 2>/dev/null; then
    echo "✅ Playwright package already installed"
else
    echo "📦 Installing Playwright package..."
    pip install playwright>=1.40.0
    echo "✅ Playwright package installed"
fi

echo ""
echo "🌐 Installing Chromium browser binaries..."
echo "   This may take a few minutes (~150-200 MB download)..."
echo ""

# Install Chromium browser with dependencies
playwright install chromium --with-deps

echo ""
echo "✅ Playwright setup complete!"
echo ""
echo "Testing installation..."
echo ""

# Test the installation
python - <<EOF
from playwright.sync_api import sync_playwright

print("🧪 Running Playwright test...")
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com", timeout=10000)
        title = page.title()
        browser.close()
        print(f"✅ Test successful! Page title: '{title}'")
        print("✅ Playwright is ready to use!")
except Exception as e:
    print(f"❌ Test failed: {e}")
    exit(1)
EOF

echo ""
echo "🚀 Next steps:"
echo "   1. Start your application: python backend.py"
echo "   2. Test URL fetching with a protected site (e.g., Best Buy)"
echo "   3. Check logs for '🎭 Using Playwright fallback' messages"
echo ""
