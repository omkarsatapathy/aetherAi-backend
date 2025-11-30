"""
Test script for the AetherAI Multi-Agent System

This script demonstrates how to use the multi-agent system with various queries.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import AgentRunner


async def test_email_agent():
    """Test the Email Agent."""
    print("\n" + "="*70)
    print("TEST 1: EMAIL AGENT")
    print("="*70)

    runner = AgentRunner()
    queries = [
        "Check my Gmail authentication status",
        "Show me my recent emails",
        "Get unread emails from the last 7 days"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = await runner.run_query(query)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_news_reader_agent():
    """Test the News Reader Agent."""
    print("\n" + "="*70)
    print("TEST 2: NEWS READER AGENT")
    print("="*70)

    runner = AgentRunner()
    queries = [
        "Give me today's top news headlines",
        "What's the latest news in technology?",
        "Provide a morning news brief"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = await runner.run_query(query)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_maps_agent():
    """Test the Maps Agent."""
    print("\n" + "="*70)
    print("TEST 3: MAPS AGENT")
    print("="*70)

    runner = AgentRunner()
    queries = [
        "Find nearby Italian restaurants",
        "What's the traffic like in Hyderabad right now?",
        "Give me directions from Gachibowli to Hitech City"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = await runner.run_query(query)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_researcher_agent():
    """Test the Researcher Agent."""
    print("\n" + "="*70)
    print("TEST 4: RESEARCHER AGENT")
    print("="*70)

    runner = AgentRunner()
    queries = [
        "Research the latest developments in quantum computing",
        "Compare different cloud storage providers",
        "Analyze the current state of electric vehicles market"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = await runner.run_query(query)
            print(f"Response: {response[:300]}...")
        except Exception as e:
            print(f"Error: {str(e)}")


async def test_coordinator_routing():
    """Test the Coordinator's routing capabilities."""
    print("\n" + "="*70)
    print("TEST 5: COORDINATOR ROUTING")
    print("="*70)

    runner = AgentRunner()

    # Create a persistent session to test routing
    session_id = await runner.create_session()

    test_cases = [
        # ("Email task", "Show my inbox"),
        ("News task", "What's in the news today?"),
        ("Maps task", "Where's a good coffee shop nearby?"),
        ("Research task", "Do a deep dive on renewable energy trends"),
        ("General chat", "Hello, how are you?")
    ]

    for test_name, query in test_cases:
        print(f"\n[{test_name}] Query: {query}")
        try:
            response = await runner.run_query(query, session_id=session_id)
            print(f"Response preview: {response[:150]}...")
        except Exception as e:
            print(f"Error: {str(e)}")


async def interactive_mode():
    """Run interactive chat session."""
    print("\n" + "="*70)
    print("INTERACTIVE MODE")
    print("="*70)

    runner = AgentRunner()
    await runner.run_interactive_session()


async def main():
    """Main test runner."""
    print("\n" + "="*70)
    print("AETHERA MULTI-AGENT SYSTEM - TEST SUITE")
    print("="*70)

    # Uncomment the tests you want to run

    # Individual agent tests
    # await test_email_agent()
    # await test_news_reader_agent()
    # await test_maps_agent()
    # await test_researcher_agent()

    # Coordinator routing test
    await test_coordinator_routing()

    # Interactive mode (comment out for automated testing)
    # await interactive_mode()

    print("\n" + "="*70)
    print("TEST SUITE COMPLETED")
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nTest suite error: {str(e)}")
        import traceback
        traceback.print_exc()
