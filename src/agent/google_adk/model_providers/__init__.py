"""ADK Model Providers Package.

This package provides model providers for Google ADK agents, supporting:
1. Google Gemini (direct string)
2. OpenAI via LiteLLM
3. Anthropic via LiteLLM
4. Ollama via LiteLLM (local models)

Usage:
    from src.agent.google_adk.model_providers import (
        ADKModelProviderFactory,
        get_adk_model
    )
    
    # Get model for LlmAgent
    model = get_adk_model("gemini-2.5-flash")
    model = get_adk_model("openai/gpt-4o")
    model = get_adk_model("ollama_chat/llama3")
"""
from .factory import ADKModelProviderFactory, get_adk_model
from .base import ADKBaseModelProvider

__all__ = [
    'ADKModelProviderFactory',
    'get_adk_model',
    'ADKBaseModelProvider',
]
