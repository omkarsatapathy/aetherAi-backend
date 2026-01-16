"""Test script for quick response endpoint."""
import requests
import json

# Test endpoint URL
BASE_URL = "http://localhost:8000"
QUICK_RESPONSE_URL = f"{BASE_URL}/api/quick-response/test"

def test_quick_response():
    """Test the quick response endpoint."""
    
    # Test payload
    payload = {
        "query": "What is the capital of France?",
        "session_id": "test-session-123"
    }
    
    print("🚀 Testing Quick Response Endpoint")
    print(f"📍 URL: {QUICK_RESPONSE_URL}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        # Make request
        response = requests.post(QUICK_RESPONSE_URL, json=payload)
        
        # Print response
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📨 Response:")
            print(f"   Model Used: {data.get('model_used')}")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"\n💬 Response Text:")
            print(f"   {data.get('response')}\n")
        else:
            print(f"\n❌ Error Response:")
            print(f"   {response.text}\n")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quick_response()
