"""Gemini model provider for ADK.

Google Gemini models are natively supported by ADK - just pass the model string directly.
"""
from typing import Union
from .base import ADKBaseModelProvider
from ....config import Config


class GeminiProvider(ADKBaseModelProvider):
    """Provider for Google Gemini models in ADK.
    
    Gemini models are directly supported by ADK via model string.
    No wrapper needed - just return the model string.
    
    Supported models:
    - gemini-2.0-flash (default)
    - gemini-2.0-flash-lite
    - gemini-2.5-pro-preview-03-25
    - gemini-1.5-pro
    - gemini-1.5-flash
    """

    # Available Gemini models
    AVAILABLE_MODELS = {
        "gemini-2.0-flash": "Gemini 2.0 Flash (Fast)",
        "gemini-2.0-flash-lite": "Gemini 2.0 Flash Lite (Fastest)",
        "gemini-2.5-pro-preview-03-25": "Gemini 2.5 Pro (Powerful)",
        "gemini-1.5-pro": "Gemini 1.5 Pro (Stable)",
        "gemini-1.5-flash": "Gemini 1.5 Flash (Stable Fast)",
    }

    def __init__(self, model_id: str = None):
        """
        Initialize Gemini provider.

        Args:
            model_id: Gemini model ID to use (default: gemini-2.0-flash)
        """
        self.model_id = model_id or Config.GEMINI_MODEL_ID or "gemini-2.0-flash"
        self._api_key = Config.GEMINI_API_KEY

    def get_model(self) -> str:
        """
        Get Gemini model string for LlmAgent.
        
        ADK natively supports Gemini - just return the model string.

        Returns:
            Gemini model ID string
        """
        return self.model_id

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "gemini"
    
    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """
        Check if Gemini is available.

        Returns:
            True if GEMINI_API_KEY or GOOGLE_API_KEY is configured
        """
        import os
        return bool(self._api_key or os.getenv("GOOGLE_API_KEY"))
    
    @classmethod
    def list_models(cls) -> dict:
        """List available Gemini models."""
        return cls.AVAILABLE_MODELS.copy()
