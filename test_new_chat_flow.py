"""Test the complete 'New Chat' flow end-to-end."""
import asyncio
import time
from src.services.firestore_service import firestore_service
import uuid

async def simulate_new_chat_flow():
    """Simulate the exact flow that happens when user clicks 'New Chat'."""
    print("\n🎯 SIMULATING 'NEW CHAT' FLOW")
    print("=" * 70)
    
    test_user_id = "test-user-" + str(uuid.uuid4())[:8]
    
    # Step 1: POST /sessions - Create session
    print("\n📍 Step 1: POST /sessions (Create new session)")
    session_id = str(uuid.uuid4())
    
    start = time.time()
    session = await firestore_service.create_session(
        user_id=test_user_id,
        session_id=session_id,
        title="New Chat"
    )
    step1_time = (time.time() - start) * 1000
    print(f"   ⏱️  Duration: {step1_time:.0f}ms")
    print(f"   ✅ Created session: {session_id}")
    
    # Step 3: GET /sessions/{session_id} - Fetch session details
    print("\n📍 Step 3: GET /sessions/{session_id} (Load session)")
    start = time.time()
    session_data = await firestore_service.get_session(
        user_id=test_user_id,
        session_id=session_id
    )
    step3_time = (time.time() - start) * 1000
    print(f"   ⏱️  Duration: {step3_time:.0f}ms")
    print(f"   ✅ Retrieved session: {session_data.get('title')}")
    
    # Also fetch messages (which the frontend typically does)
    print("\n📍 Step 3b: GET /sessions/{session_id}/messages")
    start = time.time()
    messages = await firestore_service.get_messages(
        user_id=test_user_id,
        session_id=session_id
    )
    step3b_time = (time.time() - start) * 1000
    print(f"   ⏱️  Duration: {step3b_time:.0f}ms")
    print(f"   ✅ Retrieved {len(messages)} messages")
    
    # Total time for steps 1 and 3
    total_time = step1_time + step3_time + step3b_time
    
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Step 1 (Create Session):     {step1_time:>6.0f}ms")
    print(f"Step 3 (Get Session):        {step3_time:>6.0f}ms")
    print(f"Step 3b (Get Messages):      {step3b_time:>6.0f}ms")
    print("-" * 70)
    print(f"TOTAL (excluding Step 2):    {total_time:>6.0f}ms")
    print("=" * 70)
    
    if total_time < 1000:
        print("🎉 EXCELLENT! Under 1 second!")
    elif total_time < 2000:
        print("✅ GOOD! Under 2 seconds")
    else:
        print("⚠️  Still slow, needs more optimization")
    
    print("\n💡 Note: Step 2 (quick-response) with LLM call (~2.7s) is acceptable")
    print("   and happens in parallel with other requests.")

async def test_cache_effectiveness():
    """Test that cache is working effectively."""
    print("\n\n🔄 TESTING CACHE EFFECTIVENESS")
    print("=" * 70)
    
    test_user_id = "test-user-cache"
    session_id = str(uuid.uuid4())
    
    # Create session
    await firestore_service.create_session(
        user_id=test_user_id,
        session_id=session_id,
        title="Cache Test"
    )
    
    # First retrieval (from cache - should be instant)
    print("\n1st retrieval (from cache):")
    start = time.time()
    session1 = await firestore_service.get_session(test_user_id, session_id)
    time1 = (time.time() - start) * 1000
    print(f"   ⏱️  {time1:.2f}ms")
    
    # Second retrieval (also from cache - should be instant)
    print("\n2nd retrieval (from cache):")
    start = time.time()
    session2 = await firestore_service.get_session(test_user_id, session_id)
    time2 = (time.time() - start) * 1000
    print(f"   ⏱️  {time2:.2f}ms")
    
    if time1 < 10 and time2 < 10:
        print("\n✅ Cache is working perfectly! Both retrievals < 10ms")
    else:
        print(f"\n⚠️  Cache may not be working. Times: {time1:.0f}ms, {time2:.0f}ms")

async def main():
    """Run all tests."""
    await simulate_new_chat_flow()
    await test_cache_effectiveness()
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
