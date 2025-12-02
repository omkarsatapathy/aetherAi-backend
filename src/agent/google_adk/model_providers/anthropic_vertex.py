"""Anthropic Claude on Vertex AI model provider for ADK.

This provider uses LiteLLM to wrap Anthropic's Vertex AI SDK, making it compatible
with Google ADK's agent system.

Setup:
1. Enable Vertex AI API in Google Cloud Console
2. Authenticate with Google Cloud (gcloud auth application-default login)
3. Set GCP_PROJECT_ID environment variable
4. Set GCP_LOCATION environment variable (optional, defaults to "us-east5")
5. Install dependencies: pip install 'anthropic[vertex]' litellm

Supported models:
- claude-sonnet-4@20250514 (Claude Sonnet 4 - Latest)
- claude-3-5-sonnet@20241022 (Claude 3.5 Sonnet)
- claude-3-opus@20240229 (Claude 3 Opus)
- claude-3-sonnet@20240229 (Claude 3 Sonnet)
- claude-3-haiku@20240307 (Claude 3 Haiku)

Reference: https://docs.anthropic.com/en/api/claude-on-vertex-ai
"""
import os
from typing import Any, Union
from .base import ADKBaseModelProvider
from ....logging_config import get_logger

logger = get_logger("chatbot.adk_vertex_anthropic")


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


def _setup_vertex_auth(project_id: str, location: str):
    """
    Set up authentication for Vertex AI.

    This configures environment variables needed for Anthropic's Vertex SDK.
    """
    # Set GCP environment variables for Anthropic Vertex SDK
    os.environ["CLOUD_ML_PROJECT_ID"] = project_id
    os.environ["CLOUD_ML_REGION"] = location
    os.environ["VERTEX_PROJECT"] = project_id
    os.environ["VERTEX_LOCATION"] = location


class AnthropicVertexProvider(ADKBaseModelProvider):
    """Provider for Anthropic Claude models on Google Cloud Vertex AI.

    This provider uses Anthropic's native Vertex AI SDK for direct integration
    with Google Cloud, similar to how Gemini models work natively with ADK.

    Unlike the LiteLLM-based AnthropicProvider which uses Anthropic's direct API,
    this provider routes through Google Cloud Vertex AI, which may offer:
    - Better integration with GCP services
    - Unified billing through Google Cloud
    - Access to models available through Google's Anthropic partnership

    Supported models:
    - claude-sonnet-4@20250514 (Latest, recommended)
    - claude-3-5-sonnet@20241022
    - claude-3-opus@20240229
    - claude-3-sonnet@20240229
    - claude-3-haiku@20240307

    Environment variables:
    - GCP_PROJECT_ID: Google Cloud project ID (required)
    - GCP_LOCATION: GCP region (optional, default: "us-east5")
        Available regions: "us-east5", "europe-west1", "global"
    """

    # Available Claude models on Vertex AI with pinned versions
    AVAILABLE_MODELS = {
        "claude-sonnet-4@20250514": "Claude Sonnet 4 (Latest, Pinned)",
        "claude-3-5-sonnet@20241022": "Claude 3.5 Sonnet (Pinned)",
        "claude-3-opus@20240229": "Claude 3 Opus (Pinned)",
        "claude-3-sonnet@20240229": "Claude 3 Sonnet (Pinned)",
        "claude-3-haiku@20240307": "Claude 3 Haiku (Pinned)",
        # Unpinned versions (not recommended for production)
        "claude-sonnet-4": "Claude Sonnet 4 (Unpinned)",
        "claude-3-5-sonnet": "Claude 3.5 Sonnet (Unpinned)",
        "claude-3-opus": "Claude 3 Opus (Unpinned)",
        "claude-3-sonnet": "Claude 3 Sonnet (Unpinned)",
        "claude-3-haiku": "Claude 3 Haiku (Unpinned)",
    }

    def __init__(
        self,
        model_id: str = None,
        project_id: str = None,
        location: str = None
    ):
        """
        Initialize Anthropic Vertex AI provider.

        Args:
            model_id: Claude model ID (default: claude-sonnet-4@20250514)
            project_id: GCP project ID (default: from GCP_PROJECT_ID env var)
            location: GCP region (default: from GCP_LOCATION env var or "us-east5")
        """
        # Get project ID from parameter or environment
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            logger.warning(
                "GCP_PROJECT_ID not set. Anthropic Vertex AI will not be available."
            )

        # Get location from parameter or environment
        # Note: us-east5 is a valid region for Anthropic models on Vertex AI
        self.location = location or os.getenv("GCP_LOCATION", "us-east5")

        # Get model ID and strip any provider prefixes
        raw_model_id = model_id or "claude-sonnet-4@20250514"
        
        # Strip common prefixes that might be passed from the factory
        prefixes_to_strip = [
            "anthropic-vertex/",
            "vertex-anthropic/", 
            "vertex_ai/",
        ]
        for prefix in prefixes_to_strip:
            if raw_model_id.startswith(prefix):
                raw_model_id = raw_model_id[len(prefix):]
                break
        
        # If the result is empty or just a provider name, use default
        if not raw_model_id or raw_model_id in ["anthropic-vertex", "vertex-anthropic", ""]:
            raw_model_id = "claude-sonnet-4@20250514"
        
        self.model_id = raw_model_id

        # Validate model ID
        if self.model_id not in self.AVAILABLE_MODELS:
            logger.warning(
                f"Model '{self.model_id}' not in known models list. "
                f"Available: {list(self.AVAILABLE_MODELS.keys())}"
            )

    def get_model(self) -> Union[str, Any]:
        """
        Get Anthropic Vertex AI model via LiteLLM wrapper.

        Uses LiteLLM's vertex_ai provider format for Anthropic Claude models.
        According to LiteLLM docs, Anthropic on Vertex AI uses the format:
        "vertex_ai/claude-3-5-sonnet@20241022"

        Returns:
            LiteLlm wrapper configured for Anthropic on Vertex AI
        """
        if not self.is_available():
            raise ValueError(
                "Anthropic Vertex AI is not available. "
                "Please set GCP_PROJECT_ID environment variable and ensure "
                "you have authenticated with Google Cloud. "
                "Run: gcloud auth application-default login"
            )

        # Set up Vertex AI authentication environment variables
        _setup_vertex_auth(self.project_id, self.location)

        # Use LiteLLM with vertex_ai provider for Anthropic models
        LiteLlm = _get_litellm()

        logger.info(
            f"Creating LiteLLM wrapper for Anthropic Vertex AI: "
            f"model={self.model_id}, project={self.project_id}, location={self.location}"
        )

        # LiteLLM format for Vertex AI Anthropic models: vertex_ai/<model>
        # This tells LiteLLM to use Vertex AI's Anthropic integration
        litellm_model = f"vertex_ai/{self.model_id}"

        return LiteLlm(
            model=litellm_model,
            vertex_project=self.project_id,
            vertex_location=self.location
        )

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic-vertex"

    def get_model_id(self) -> str:
        """Get model ID."""
        return self.model_id

    def is_available(self) -> bool:
        """
        Check if Anthropic Vertex AI is available.

        Checks:
        1. GCP_PROJECT_ID is set
        2. LiteLLM is installed
        3. Google Cloud authentication is configured

        Returns:
            True if Anthropic Vertex AI can be used, False otherwise
        """
        # Check if project ID is configured
        if not self.project_id:
            logger.debug("Anthropic Vertex AI not available: GCP_PROJECT_ID not set")
            return False

        # Check if LiteLLM is installed
        try:
            _get_litellm()
        except ImportError:
            logger.debug(
                "Anthropic Vertex AI not available: litellm not installed"
            )
            return False

        # Check if Google Cloud credentials are available
        try:
            import google.auth
            credentials, project = google.auth.default()
            logger.debug(
                f"Anthropic Vertex AI available: "
                f"project={self.project_id}, location={self.location}"
            )
            return True
        except Exception as e:
            logger.debug(
                f"Anthropic Vertex AI not available: "
                f"Google Cloud authentication failed: {e}"
            )
            return False

    @classmethod
    def list_models(cls) -> dict:
        """List available Anthropic Vertex AI models."""
        return cls.AVAILABLE_MODELS.copy()
