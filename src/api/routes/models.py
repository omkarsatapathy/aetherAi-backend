"""Model provider endpoints."""
from fastapi import APIRouter
from src.agent.google_adk import ADKModelProviderFactory
from src.config import Config
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.models")

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/providers")
async def get_providers():
    """
    Get list of available model providers (Google ADK).

    Returns:
        Dictionary with available providers and default provider
    """
    try:
        providers = ADKModelProviderFactory.get_available_providers()
        default_provider = ADKModelProviderFactory.get_default_provider()
        default_model = ADKModelProviderFactory.get_default_model()

        return {
            "providers": providers,
            "default": default_provider,
            "default_model": default_model
        }
    except Exception as e:
        logger.error(f"Error getting providers: {e}", exc_info=True)
        return {
            "providers": [],
            "default": None,
            "default_model": None,
            "error": str(e)
        }


@router.get("/styles")
async def get_response_styles():
    """
    Get available response styles.

    Returns:
        Dictionary with available styles and default style
    """
    try:
        styles = list(Config.RESPONSE_STYLES.keys())
        return {
            "styles": styles,
            "default": Config.DEFAULT_RESPONSE_STYLE,
            "descriptions": {
                "Normal": "Default balanced responses",
                "Formal": "Professional, business-appropriate tone",
                "Explanatory": "Detailed explanations with examples",
                "Concise": "Brief, to-the-point responses",
                "Learning": "Teaching style with simple explanations"
            }
        }
    except Exception as e:
        logger.error(f"Error getting styles: {e}", exc_info=True)
        return {
            "styles": ["Normal"],
            "default": "Normal",
            "error": str(e)
        }
