"""Test authentication setup for ADK"""
from src.agent.google_adk.runner_setup import ADKAgentRunner
import os

print("=" * 60)
print("AUTHENTICATION SETUP TEST")
print("=" * 60)

print("\nBefore ADKAgentRunner init:")
print(f"  GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'NOT SET')}")
print(f"  GEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
print(f"  GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
print(f"  GOOGLE_CLOUD_PROJECT: {'SET' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'NOT SET'}")

print("\n" + "=" * 60)
print("Initializing ADKAgentRunner...")
print("=" * 60)

try:
    runner = ADKAgentRunner()
    
    print("\n✅ ADKAgentRunner initialized successfully!")
    print("\nAfter ADKAgentRunner init:")
    print(f"  GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'NOT SET')}")
    print(f"  GEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
    print(f"  GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
    print(f"  GOOGLE_CLOUD_PROJECT: {'SET' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'NOT SET'}")
    
    print("\n" + "=" * 60)
    if os.getenv('GOOGLE_CLOUD_PROJECT'):
        print("✅ CONFIGURED FOR VERTEX AI AUTHENTICATION")
        print(f"   Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
        print("   ✓ No API rate limits!")
        print("   ✓ ADK Agent uses Vertex AI")
        print("   ✓ Code Generation Tool uses Vertex AI")
    elif os.getenv('GOOGLE_API_KEY'):
        print("⚠️  CONFIGURED FOR API KEY AUTHENTICATION")
        print("   ⚠️  May encounter 503 rate limit errors")
        print("   Consider setting GCP_PROJECT_ID for Vertex AI")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
