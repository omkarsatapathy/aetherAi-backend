"""ADK Model Providers Package.

This package provides model providers for Google ADK agents, supporting:
1. Google Gemini (direct string)
2. Anthropic Claude via Google Cloud Vertex AI (native SDK)
3. OpenAI via LiteLLM
4. Anthropic via LiteLLM (direct API)
5. Ollama via LiteLLM (local models)

Usage:
    from src.agent.google_adk.model_providers import (
        ADKModelProviderFactory,
        get_adk_model
    )

    # Get model for LlmAgent
    model = get_adk_model("gemini-2.5-flash")
    model = get_adk_model("anthropic-vertex/claude-sonnet-4@20250514")
    model = get_adk_model("openai/gpt-4o")
    model = get_adk_model("anthropic/claude-3-5-sonnet-20241022")
    model = get_adk_model("ollama_chat/llama3")
"""
from .factory import ADKModelProviderFactory, get_adk_model
from .base import ADKBaseModelProvider

__all__ = [
    'ADKModelProviderFactory',
    'get_adk_model',
    'ADKBaseModelProvider',
]
