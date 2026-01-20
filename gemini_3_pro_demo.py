"""
Simple Gemini 3 Pro Invocation Demo with Streaming
Using Google's official genai SDK

pip install google-genai
"""

from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig

# Initialize client for Vertex AI
client = genai.Client(vertexai=True, project="effortless-lock-329115", location="global")


def call_gemini_3_pro_stream(prompt: str, thinking_level: str = "HIGH"):
    """
    Call Gemini 3 Pro with streaming using official SDK

    Args:
        prompt: The prompt to send
        thinking_level: "LOW" or "HIGH"
    """
    config = GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_level=thinking_level)
    )

    for chunk in client.models.generate_content_stream(
        model="gemini-3-pro-preview",
        contents=prompt,
        config=config,
    ):
        if chunk.text:
            print(chunk.text, end="", flush=True)


if __name__ == "__main__":
    prompt = "Write a python code in pytorch to build a deep neural network for MNIST dataset"

    print("=" * 60)
    print("Gemini 3 Pro Demo - Streaming with Thinking (HIGH)")
    print("=" * 60)
    print(f"\nPrompt: {prompt}\n")
    print("-" * 60)
    print("Response:\n")

    call_gemini_3_pro_stream(prompt, thinking_level="HIGH")

    print()  # Final newline
