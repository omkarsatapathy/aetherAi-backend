"""Test performance bottlenecks in session endpoints."""
import asyncio
import time
from src.services.firestore_service import firestore_service
from src.firebase_admin_config import verify_token
import uuid

async def test_token_verification():
    """Test token verification speed (requires a valid token)."""
    print("⏱️  Testing Token Verification...")
    # This would need a real token - just showing structure
    print("   (Skipped - requires valid token from frontend)")
    
async def test_session_creation():
    """Test session creation speed."""
    print("\n⏱️  Testing Session Creation...")
    
    # Use a test user ID
    test_user_id = "test-user-perf-" + str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    start = time.time()
    session = await firestore_service.create_session(
        user_id=test_user_id,
        session_id=session_id,
        title="Test Session"
    )
    duration = (time.time() - start) * 1000  # Convert to ms
    
    print(f"   ✅ Session created in {duration:.2f}ms")
    print(f"   Session data: {session}")
    
    return test_user_id, session_id

async def test_session_retrieval(user_id: str, session_id: str):
    """Test session retrieval speed."""
    print("\n⏱️  Testing Session Retrieval...")
    
    start = time.time()
    session = await firestore_service.get_session(
        user_id=user_id,
        session_id=session_id
    )
    duration = (time.time() - start) * 1000
    
    print(f"   ✅ Session retrieved in {duration:.2f}ms")
    print(f"   Session data: {session}")

async def test_message_retrieval(user_id: str, session_id: str):
    """Test message retrieval speed."""
    print("\n⏱️  Testing Message Retrieval (empty session)...")
    
    start = time.time()
    messages = await firestore_service.get_messages(
        user_id=user_id,
        session_id=session_id
    )
    duration = (time.time() - start) * 1000
    
    print(f"   ✅ Messages retrieved in {duration:.2f}ms")
    print(f"   Message count: {len(messages)}")

async def main():
    """Run performance tests."""
    print("🚀 Starting Performance Tests\n")
    print("=" * 60)
    
    # Test token verification
    await test_token_verification()
    
    # Test session creation
    user_id, session_id = await test_session_creation()
    
    # Test session retrieval
    await test_session_retrieval(user_id, session_id)
    
    # Test message retrieval
    await test_message_retrieval(user_id, session_id)
    
    print("\n" + "=" * 60)
    print("✅ Performance tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
