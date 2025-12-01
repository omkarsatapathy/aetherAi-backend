"""Base class for ADK model providers."""
from abc import ABC, abstractmethod
from typing import Any, Union


class ADKBaseModelProvider(ABC):
    """Abstract base class for ADK model providers.
    
    ADK supports models via:
    1. Direct string (Gemini models): "gemini-2.5-flash"
    2. LiteLlm wrapper (OpenAI, Anthropic, Ollama, etc.)
    3. Vertex AI endpoints: "projects/.../endpoints/..."
    """

    @abstractmethod
    def get_model(self) -> Union[str, Any]:
        """
        Get the model for LlmAgent.

        Returns:
            Either a model string (for Gemini) or a LiteLlm wrapper instance
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider.

        Returns:
            Provider name (e.g., 'gemini', 'openai', 'ollama')
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured and available.

        Returns:
            True if the provider can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_id(self) -> str:
        """
        Get the model ID string.

        Returns:
            Model identifier string
        """
        pass
