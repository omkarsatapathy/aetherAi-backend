"""Test script for JSON Structure Enforcer functionality."""
import asyncio
from src.utils.json_structure_enforcer import get_json_enforcer


def test_shopping_preference_extraction():
    """Test shopping preference JSON extraction."""
    print("\n" + "="*80)
    print("Testing Shopping Preference JSON Extraction")
    print("="*80)

    # Test case 1: Valid JSON in code block
    response1 = """
    Let me help you find the perfect laptop! Answer a few quick questions:

    ```json
    {
        "agent_message": "Let me help you find the perfect laptop! Answer a few quick questions:",
        "questions": [
            {
                "question": "What's your budget range?",
                "options": ["Under $500", "$500-$1000", "$1000-$2000", "Above $2000"]
            },
            {
                "question": "What will you primarily use it for?",
                "options": ["Gaming", "Work/Productivity", "Content Creation", "General Use"]
            }
        ]
    }
    ```
    """

    # Test case 2: Malformed JSON (missing proper structure)
    response2 = """
    I can help you find a great laptop! Here are some questions:

    1. What's your budget?
    - Under $500
    - $500-$1000
    - Above $1000

    2. Primary use case?
    - Gaming
    - Work
    - General use
    """

    # Test case 3: JSON without code block markers
    response3 = """
    {"agent_message": "Let me help you!", "questions": [{"question": "Budget?", "options": ["Low", "Medium", "High"]}]}
    """

    enforcer = get_json_enforcer()

    print("\n[Test 1] Valid JSON in code block:")
    result1 = enforcer.extract_shopping_preference_json(response1)
    if result1:
        print("✅ SUCCESS")
        print(f"   Message: {result1['agent_message']}")
        print(f"   Questions: {len(result1['questions'])}")
    else:
        print("❌ FAILED")

    print("\n[Test 2] Malformed JSON (requires LLM extraction):")
    result2 = enforcer.extract_shopping_preference_json(response2)
    if result2:
        print("✅ SUCCESS")
        print(f"   Message: {result2['agent_message']}")
        print(f"   Questions: {len(result2['questions'])}")
    else:
        print("❌ FAILED")

    print("\n[Test 3] JSON without code blocks:")
    result3 = enforcer.extract_shopping_preference_json(response3)
    if result3:
        print("✅ SUCCESS")
        print(f"   Message: {result3['agent_message']}")
        print(f"   Questions: {len(result3['questions'])}")
    else:
        print("❌ FAILED")


def test_product_summary_extraction():
    """Test product summary JSON extraction."""
    print("\n" + "="*80)
    print("Testing Product Summary JSON Extraction")
    print("="*80)

    # Test case 1: Valid JSON in code block
    response1 = """
    Based on your preferences, I found 3 excellent laptops! Here are my recommendations:

    ```json
    {
        "products": [
            {
                "text_response": "The Dell XPS 15 is perfect for your needs. It features a powerful Intel i7 processor, 16GB RAM, and 512GB SSD. Great for productivity and light gaming.",
                "image_link": "https://example.com/dell-xps-15.jpg",
                "product_link": "https://amazon.com/dell-xps-15"
            },
            {
                "text_response": "MacBook Pro 14 offers excellent performance with M3 chip, 16GB unified memory, and stunning Retina display. Ideal for creative work.",
                "image_link": "https://example.com/macbook-pro.jpg",
                "product_link": "https://apple.com/macbook-pro"
            }
        ]
    }
    ```
    """

    # Test case 2: Unstructured product list
    response2 = """
    I found these great laptops for you:

    1. Dell XPS 15 - $1299
       - Intel i7, 16GB RAM, 512GB SSD
       - Perfect for work and gaming
       - Buy at: https://amazon.com/dell-xps

    2. MacBook Pro 14 - $1999
       - M3 chip, 16GB memory
       - Great for creative work
       - Buy at: https://apple.com/macbook
    """

    enforcer = get_json_enforcer()

    print("\n[Test 1] Valid JSON in code block:")
    result1 = enforcer.extract_product_summary_json(response1)
    if result1:
        print("✅ SUCCESS")
        print(f"   Products: {len(result1['products'])}")
        for i, prod in enumerate(result1['products'], 1):
            print(f"   Product {i}: {prod['text_response'][:50]}...")
    else:
        print("❌ FAILED")

    print("\n[Test 2] Unstructured product list (requires LLM extraction):")
    result2 = enforcer.extract_product_summary_json(response2)
    if result2:
        print("✅ SUCCESS")
        print(f"   Products: {len(result2['products'])}")
        for i, prod in enumerate(result2['products'], 1):
            print(f"   Product {i}: {prod['text_response'][:50]}...")
    else:
        print("❌ FAILED")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("JSON Structure Enforcer Test Suite")
    print("="*80)

    try:
        # Run tests
        test_shopping_preference_extraction()
        test_product_summary_extraction()

        print("\n" + "="*80)
        print("Test Suite Completed")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
