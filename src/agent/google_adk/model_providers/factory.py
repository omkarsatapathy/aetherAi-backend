"""Factory for creating ADK model provider instances.

This factory supports:
1. Google Gemini (native ADK support)
2. OpenAI (via LiteLLM)
3. Anthropic (via LiteLLM)
4. Ollama (via LiteLLM)
5. LlamaCpp (via LiteLLM OpenAI-compatible)

Usage:
    from src.agent.google_adk.model_providers import get_adk_model
    
    # Get model for LlmAgent
    model = get_adk_model("gemini-2.5-flash")
    model = get_adk_model("openai/gpt-4o")
    model = get_adk_model("anthropic/claude-3-5-sonnet-20241022")
    model = get_adk_model("ollama_chat/llama3.2")
"""
from typing import Any, Optional, Union
from .base import ADKBaseModelProvider
from .gemini import GeminiProvider
from .anthropic_vertex import AnthropicVertexProvider
from .litellm_providers import (
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    LlamaCppProvider
)
from ....logging_config import get_logger

logger = get_logger("chatbot.adk_model_factory")


class ADKModelProviderFactory:
    """Factory for creating ADK model provider instances."""

    # Registry of available providers with their prefixes
    _provider_prefixes = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        # "anthropic": AnthropicProvider,
        "anthropic-vertex": AnthropicVertexProvider,  # Claude via Google Cloud Vertex AI
        "vertex-anthropic": AnthropicVertexProvider,  # Alias
        # "ollama_chat": OllamaProvider,
        # "ollama": OllamaProvider,  # Redirect to ollama_chat
        # "llamacpp": LlamaCppProvider,
    }
    
    # Default models for each provider
    _default_models = {
        "gemini": "gemini-2.5-flash",
        "openai": "openai/gpt-4o",
        "anthropic": "anthropic/claude-3-5-sonnet-20241022",
        "anthropic-vertex": "anthropic-vertex/claude-sonnet-4@20250514",
        "vertex-anthropic": "anthropic-vertex/claude-sonnet-4@20250514",
        # "ollama_chat": "ollama_chat/llama3.2",
        # "ollama": "ollama_chat/llama3.2",
        # "llamacpp": "openai/local-model",
    }

    @classmethod
    def create_provider(cls, model_string: str) -> ADKBaseModelProvider:
        """
        Create a model provider instance from a model string.

        Args:
            model_string: Model identifier string, e.g.:
                - "gemini-2.5-flash" (Gemini)
                - "openai/gpt-4o" (OpenAI)
                - "anthropic/claude-3-5-sonnet-20241022" (Anthropic)
                - "ollama_chat/llama3.2" (Ollama)
                - "llamacpp" (local llama.cpp)

        Returns:
            Initialized provider instance

        Raises:
            ValueError: If provider is not recognized or not available
        """
        model_string = model_string.strip()

        # Determine provider from model string
        provider_name = cls._detect_provider(model_string)

        if provider_name not in cls._provider_prefixes:
            available = ", ".join(cls._provider_prefixes.keys())
            raise ValueError(
                f"Unknown provider for model '{model_string}'. "
                f"Available providers: {available}"
            )

        # Create provider instance with the model ID
        provider_class = cls._provider_prefixes[provider_name]

        # Handle case where user passes just the provider name (e.g., "anthropic-vertex")
        # In this case, use the default model for that provider
        if model_string in cls._provider_prefixes or model_string.lower() in cls._provider_prefixes:
            # User passed just provider name, use default model
            default_model = cls._default_models.get(provider_name)
            if default_model:
                logger.info(f"Provider name '{model_string}' detected, using default model: {default_model}")
                model_string = default_model

        # Handle Ollama redirect
        if provider_name == "ollama" and not model_string.startswith("ollama_chat/"):
            # Convert ollama/model to ollama_chat/model for proper tool support
            if "/" in model_string:
                model_string = model_string.replace("ollama/", "ollama_chat/", 1)
            else:
                model_string = f"ollama_chat/{model_string}"

        provider = provider_class(model_id=model_string)
        
        logger.info(f"Created {provider_name} provider for model: {model_string}")
        return provider
    
    @classmethod
    def _detect_provider(cls, model_string: str) -> str:
        """
        Detect the provider from a model string.

        Args:
            model_string: Model identifier string

        Returns:
            Provider name
        """
        model_lower = model_string.lower()

        # Check if user passed just a provider name (e.g., "anthropic-vertex", "openai")
        if model_lower in cls._provider_prefixes:
            return model_lower

        # Check for explicit provider prefix (e.g., "openai/gpt-4o", "anthropic-vertex/claude-sonnet-4")
        if "/" in model_string:
            prefix = model_string.split("/")[0].lower()
            if prefix in cls._provider_prefixes:
                return prefix

        # Check for Gemini models (no prefix needed)
        if model_lower.startswith("gemini"):
            return "gemini"

        # Check for specific patterns
        if "gpt" in model_lower:
            return "openai"

        # Check for Claude models - distinguish between Vertex AI and Direct API
        if "claude" in model_lower:
            # If it has @timestamp (e.g., claude-sonnet-4@20250514), it's Vertex AI
            if "@" in model_string:
                return "anthropic-vertex"
            # Otherwise, default to Direct API
            return "anthropic"

        if "llama" in model_lower or "mistral" in model_lower or "qwen" in model_lower:
            return "ollama_chat"

        # Default to Gemini for unknown models
        logger.warning(f"Unknown model pattern '{model_string}', defaulting to Gemini")
        return "gemini"

    @classmethod
    def get_model(cls, model_string: str) -> Union[str, Any]:
        """
        Get the model object/string for use with LlmAgent.

        This is a convenience method that creates a provider and returns the model.

        Args:
            model_string: Model identifier string

        Returns:
            Model object (LiteLlm wrapper) or string (for Gemini)

        Raises:
            ValueError: If provider is not available
        """
        provider = cls.create_provider(model_string)
        
        if not provider.is_available():
            raise ValueError(
                f"Provider '{provider.get_provider_name()}' is not available. "
                f"Please check your configuration (API keys, server status)."
            )
        
        return provider.get_model()

    @classmethod
    def get_available_providers(cls) -> list[dict[str, Any]]:
        """
        Get list of available and configured providers.

        Returns:
            List of dicts with provider info
        """
        providers = []
        seen_providers = set()
        
        provider_display_names = {
            "gemini": "Google Gemini",
            "openai": "OpenAI (Direct API)",
            # "anthropic": "Anthropic Claude (Direct API)",
            "anthropic-vertex": "Anthropic Claude",
            # "ollama_chat": "Ollama (Local)",
            # "llamacpp": "LlamaCpp (Local)",
        }

        for name, provider_class in cls._provider_prefixes.items():
            # Skip duplicates (ollama is alias for ollama_chat, vertex-anthropic is alias)
            if name in ("ollama", "vertex-anthropic"):
                continue
            if name in seen_providers:
                continue
            seen_providers.add(name)
            
            try:
                provider = provider_class()
                is_available = provider.is_available()
                models = provider_class.list_models() if hasattr(provider_class, 'list_models') else {}
            except Exception as e:
                logger.debug(f"Error checking provider {name}: {e}")
                is_available = False
                models = {}

            providers.append({
                "name": name,
                "display_name": provider_display_names.get(name, name),
                "available": is_available,
                "default_model": cls._default_models.get(name, ""),
                "models": models,
            })

        return providers

    @classmethod
    def get_default_provider(cls) -> str:
        """
        Get the default provider name.

        Returns the first available provider in priority order:
        1. Gemini (most integrated with ADK)
        2. OpenAI
        3. Anthropic Vertex AI - Claude Sonnet 4 (Google Cloud integration)
        4. Anthropic Direct API
        5. Ollama
        6. LlamaCpp
        """
        priority = ["gemini", "openai", "anthropic-vertex", "anthropic", "ollama_chat", "llamacpp"]
        
        for provider_name in priority:
            try:
                provider_class = cls._provider_prefixes.get(provider_name)
                if provider_class:
                    provider = provider_class()
                    if provider.is_available():
                        return provider_name
            except Exception:
                continue
        
        # Default to Gemini even if not available
        return "gemini"
    
    @classmethod
    def get_default_model(cls) -> str:
        """
        Get the default model string.
        
        Returns:
            Default model string for the best available provider
        """
        default_provider = cls.get_default_provider()
        return cls._default_models.get(default_provider, "gemini-2.5-flash")


# Convenience function
def get_adk_model(model_string: str) -> Union[str, Any]:
    """
    Get the model object/string for use with LlmAgent.
    
    This is a convenience function that wraps the factory.
    
    Args:
        model_string: Model identifier string, e.g.:
            - "gemini-2.5-flash" (Gemini)
            - "openai/gpt-4o" (OpenAI via LiteLLM)
            - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
            - "ollama_chat/llama3.2" (Ollama via LiteLLM)
    
    Returns:
        Model object or string for LlmAgent
        
    Example:
        from google.adk.agents import LlmAgent
        from src.agent.google_adk.model_providers import get_adk_model
        
        agent = LlmAgent(
            model=get_adk_model("openai/gpt-4o"),
            name="my_agent",
            instruction="You are a helpful assistant."
        )
    """
    return ADKModelProviderFactory.get_model(model_string)
