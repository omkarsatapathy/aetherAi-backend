"""LiteLLM-based model providers for ADK.

This module provides access to various LLMs through LiteLLM:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3)
- Ollama (Local models)

LiteLLM acts as a translation layer with OpenAI-compatible interface.

Reference: https://google.github.io/adk-docs/agents/models/#using-cloud-proprietary-models-via-litellm
"""
import os
from typing import Any, Optional
from .base import ADKBaseModelProvider
from ....config import Config
from ....logging_config import get_logger

logger = get_logger("chatbot.adk_model_providers")


def _get_litellm():
    """Lazy import of LiteLlm to avoid import errors if not installed."""
    try:
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm
    except ImportError:
        raise ImportError(
            "LiteLLM integration requires 'litellm' package. "
            "Install with: pip install litellm"
        )


class OpenAIProvider(ADKBaseModelProvider):
    """Provider for OpenAI models via LiteLLM.
    
    Requires OPENAI_API_KEY environment variable.
    
    Supported models:
    - openai/gpt-4o (default)
    - openai/gpt-4-turbo
    - openai/gpt-4
    - openai/gpt-3.5-turbo
    """

    AVAILABLE_MODELS = {
        "openai/gpt-4o": "GPT-4o (Latest)",
        "openai/gpt-4o-mini": "GPT-4o Mini (Fast)",
        "openai/gpt-4-turbo": "GPT-4 Turbo",
        "openai/gpt-4": "GPT-4",
        "openai/gpt-3.5-turbo": "GPT-3.5 Turbo (Economy)",
    }

    def __init__(self, model_id: str = None):
        """
        Initialize OpenAI provider.

        Args:
            model_id: OpenAI model ID (default: openai/gpt-4o)
        """
        self.model_id = model_id or "openai/gpt-4o"
        self._api_key = os.getenv("OPENAI_API_KEY")

    def get_model(self) -> Any:
        """
        Get OpenAI model via LiteLLM wrapper.

        Returns:
            LiteLlm wrapper configured for OpenAI
        """
        LiteLlm = _get_litellm()
        return LiteLlm(model=self.model_id)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"
    
    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """Check if OpenAI is available (API key configured)."""
        return bool(self._api_key)
    
    @classmethod
    def list_models(cls) -> dict:
        """List available OpenAI models."""
        return cls.AVAILABLE_MODELS.copy()


class AnthropicProvider(ADKBaseModelProvider):
    """Provider for Anthropic Claude models via LiteLLM.
    
    Requires ANTHROPIC_API_KEY environment variable.
    
    Supported models:
    - anthropic/claude-3-5-sonnet-20241022 (default)
    - anthropic/claude-3-opus-20240229
    - anthropic/claude-3-sonnet-20240229
    - anthropic/claude-3-haiku-20240307
    """

    AVAILABLE_MODELS = {
        "anthropic/claude-sonnet-4-20250514": "Claude Sonnet 4 (Latest)",
        "anthropic/claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Balanced)",
        "anthropic/claude-3-opus-20240229": "Claude 3 Opus (Powerful)",
        "anthropic/claude-3-sonnet-20240229": "Claude 3 Sonnet",
        "anthropic/claude-3-haiku-20240307": "Claude 3 Haiku (Fast)",
    }

    def __init__(self, model_id: str = None):
        """
        Initialize Anthropic provider.

        Args:
            model_id: Anthropic model ID (default: claude-3-5-sonnet)
        """
        self.model_id = model_id or "anthropic/claude-3-5-sonnet-20241022"
        self._api_key = os.getenv("ANTHROPIC_API_KEY")

    def get_model(self) -> Any:
        """
        Get Anthropic model via LiteLLM wrapper.

        Returns:
            LiteLlm wrapper configured for Anthropic
        """
        LiteLlm = _get_litellm()
        return LiteLlm(model=self.model_id)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"
    
    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """Check if Anthropic is available (API key configured)."""
        return bool(self._api_key)
    
    @classmethod
    def list_models(cls) -> dict:
        """List available Anthropic models."""
        return cls.AVAILABLE_MODELS.copy()


class OllamaProvider(ADKBaseModelProvider):
    """Provider for Ollama local models via LiteLLM.
    
    Requires Ollama server running locally.
    Set OLLAMA_API_BASE environment variable (default: http://localhost:11434)
    
    Important: Use 'ollama_chat' provider for proper tool support!
    
    Supported models (depends on what you have pulled):
    - ollama_chat/llama3.2 (default)
    - ollama_chat/mistral-small3.1
    - ollama_chat/qwen2.5:7b
    - ollama_chat/phi3
    """

    AVAILABLE_MODELS = {
        "ollama_chat/llama3.2": "Llama 3.2 (Local)",
        "ollama_chat/llama3.1": "Llama 3.1 (Local)",
        "ollama_chat/mistral-small3.1": "Mistral Small 3.1 (Local)",
        "ollama_chat/qwen2.5:7b": "Qwen 2.5 7B (Local)",
        "ollama_chat/phi3": "Phi-3 (Local)",
        "ollama_chat/gemma2": "Gemma 2 (Local)",
    }

    def __init__(self, model_id: str = None, api_base: str = None):
        """
        Initialize Ollama provider.

        Args:
            model_id: Ollama model ID (default: ollama_chat/llama3.2)
            api_base: Ollama API base URL (default: from OLLAMA_API_BASE or localhost:11434)
        """
        self.model_id = model_id or "ollama_chat/llama3.2"
        self.api_base = api_base or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        
        # Ensure OLLAMA_API_BASE is set for LiteLLM
        if not os.getenv("OLLAMA_API_BASE"):
            os.environ["OLLAMA_API_BASE"] = self.api_base

    def get_model(self) -> Any:
        """
        Get Ollama model via LiteLLM wrapper.

        Returns:
            LiteLlm wrapper configured for Ollama
        """
        LiteLlm = _get_litellm()
        return LiteLlm(model=self.model_id)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "ollama"
    
    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """
        Check if Ollama server is available.
        
        Attempts to connect to the Ollama API.
        """
        import urllib.request
        import urllib.error
        
        try:
            url = f"{self.api_base}/api/tags"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, Exception) as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    @classmethod
    def list_models(cls) -> dict:
        """List available Ollama models (predefined list)."""
        return cls.AVAILABLE_MODELS.copy()


class LlamaCppProvider(ADKBaseModelProvider):
    """Provider for llama.cpp server via LiteLLM's OpenAI-compatible interface.
    
    Requires llama.cpp server running with OpenAI-compatible API.
    Set environment variables:
    - OPENAI_API_BASE=http://localhost:8080/v1
    - OPENAI_API_KEY=anything (can be dummy)
    
    This uses LiteLLM's 'openai' provider to connect to llama.cpp.
    """

    def __init__(self, model_id: str = None, api_base: str = None):
        """
        Initialize llama.cpp provider.

        Args:
            model_id: Model name (used for display, default: local-model)
            api_base: llama.cpp API base URL (default: from LLAMACPP_API_BASE or localhost:8080)
        """
        self.model_id = model_id or "openai/local-model"
        self.api_base = api_base or os.getenv("LLAMACPP_API_BASE", "http://localhost:8080/v1")
        
        # Set OpenAI env vars for LiteLLM
        os.environ.setdefault("OPENAI_API_BASE", self.api_base)
        os.environ.setdefault("OPENAI_API_KEY", "llamacpp-local")

    def get_model(self) -> Any:
        """
        Get llama.cpp model via LiteLLM's OpenAI wrapper.

        Returns:
            LiteLlm wrapper configured for llama.cpp server
        """
        LiteLlm = _get_litellm()
        return LiteLlm(
            model=self.model_id,
            api_base=self.api_base
        )

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "llamacpp"
    
    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """
        Check if llama.cpp server is available.
        """
        import urllib.request
        import urllib.error
        
        try:
            url = f"{self.api_base}/models"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, Exception) as e:
            logger.debug(f"llama.cpp not available: {e}")
            return False
