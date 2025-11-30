#!/usr/bin/env python3
"""
Quick Gmail OAuth Testing Script

This script helps you quickly test the Gmail OAuth implementation.
Run this after setting up your environment variables.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gmail.auth_manager import GmailAuthManager
from src.gmail.credentials_manager import GmailCredentialsManager
from src.firebase_admin_config import initialize_firebase


def test_environment():
    """Test that environment variables are set."""
    print("=" * 60)
    print("STEP 1: Checking Environment Variables")
    print("=" * 60)

    required_vars = {
        'GOOGLE_OAUTH_CLIENT_CONFIG': os.getenv('GOOGLE_OAUTH_CLIENT_CONFIG'),
        'GMAIL_TOKEN_ENCRYPTION_KEY': os.getenv('GMAIL_TOKEN_ENCRYPTION_KEY'),
    }

    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: Set (length: {len(var_value)})")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False

    if not all_set:
        print("\n⚠️  Missing environment variables!")
        print("Please set them in your .env file or environment.")
        return False

    print("\n✅ All required environment variables are set!\n")
    return True


def test_firebase():
    """Test Firebase initialization."""
    print("=" * 60)
    print("STEP 2: Testing Firebase Connection")
    print("=" * 60)

    try:
        app = initialize_firebase()
        if app:
            print("✅ Firebase initialized successfully!")
            return True
        else:
            print("⚠️  Firebase initialized but app is None (might be using ADC)")
            return True
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False


def test_oauth_config():
    """Test OAuth configuration."""
    print("\n" + "=" * 60)
    print("STEP 3: Testing OAuth Configuration")
    print("=" * 60)

    try:
        auth_manager = GmailAuthManager()
        print("✅ GmailAuthManager initialized successfully!")

        # Test client config
        if auth_manager.client_config:
            client_id = auth_manager.client_config.get('web', {}).get('client_id', 'Not found')
            print(f"✅ OAuth Client ID: {client_id[:50]}...")
            return True
        else:
            print("❌ OAuth client config not loaded")
            return False

    except FileNotFoundError as e:
        print(f"❌ OAuth config file not found: {e}")
        print("\n📝 Make sure GOOGLE_OAUTH_CLIENT_CONFIG is set with valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error initializing auth manager: {e}")
        return False


def test_encryption():
    """Test encryption setup."""
    print("\n" + "=" * 60)
    print("STEP 4: Testing Encryption")
    print("=" * 60)

    try:
        creds_manager = GmailCredentialsManager()

        # Test encryption/decryption
        test_data = "test_secret_token_12345"
        encrypted = creds_manager._encrypt(test_data)
        decrypted = creds_manager._decrypt(encrypted)

        if decrypted == test_data:
            print("✅ Encryption/Decryption working correctly!")
            print(f"   Original:  {test_data}")
            print(f"   Encrypted: {encrypted[:50]}...")
            print(f"   Decrypted: {decrypted}")
            return True
        else:
            print("❌ Encryption/Decryption mismatch!")
            return False

    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False


def generate_test_url():
    """Generate test URL for manual OAuth testing."""
    print("\n" + "=" * 60)
    print("STEP 5: Manual OAuth Test")
    print("=" * 60)

    try:
        auth_manager = GmailAuthManager()

        # For testing, use a test user ID
        test_user_id = "test-user-123"
        redirect_uri = "http://localhost:8080/api/auth/gmail/callback"

        auth_url = auth_manager.get_authorization_url(test_user_id, redirect_uri)

        print("✅ OAuth URL generated successfully!")
        print("\n📝 To test OAuth flow manually:")
        print("   1. Start your backend server:")
        print("      python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8080")
        print("\n   2. Open this URL in your browser:")
        print(f"      {auth_url}")
        print("\n   3. Complete the Google OAuth flow")
        print("   4. You should be redirected back with success message")

        return True

    except Exception as e:
        print(f"❌ Failed to generate OAuth URL: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Gmail OAuth Quick Test")
    print("=" * 60)
    print("This script will verify your Gmail OAuth setup.\n")

    tests = [
        ("Environment Variables", test_environment),
        ("Firebase Connection", test_firebase),
        ("OAuth Configuration", test_oauth_config),
        ("Encryption System", test_encryption),
        ("OAuth URL Generation", generate_test_url),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your Gmail OAuth setup is ready.")
        print("\n📝 Next steps:")
        print("   1. Start your backend server")
        print("   2. Test the OAuth flow in your browser")
        print("   3. See GMAIL_TESTING_GUIDE.md for detailed testing")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("   See GMAIL_SETUP_GUIDE.md for configuration help.")

    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
