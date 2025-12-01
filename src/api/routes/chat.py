"""Chat streaming endpoint."""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from src.api.models import ChatRequest
from src.agent.streaming_agent import create_streaming_response
from src.agent.google_adk import create_adk_streaming_response, ADKModelProviderFactory
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger
from src.config import Config
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

logger = get_logger("chatbot.routes.chat")

router = APIRouter(prefix="/api", tags=["chat"])


# Add/update the request model to match what Swagger expects
class ChatStreamRequest(BaseModel):
    """Request model for chat streaming that matches frontend payload."""
    message: str  # For Swagger UI - simple message
    session_id: Optional[str] = None
    model_provider: Optional[str] = Config.GEMINI_MODEL_ID
    response_style: Optional[str] = "Normal"
    web_search: bool = False
    conversation_history: List[Dict[str, Any]] = []
    
    # Alternative fields for direct message object (from frontend)
    id: Optional[int] = None
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/chat/stream")
async def chat_stream_post(request: ChatStreamRequest, current_user: dict = Depends(get_current_user)):
    """
    Stream chat responses with real-time tool execution updates (POST).
    Requires Firebase Authentication.
    """
    # Extract user_id from authenticated token
    user_id = get_user_id_from_token(current_user)

    # Handle both formats
    message = request.content if request.content else request.message
    session_id = request.session_id

    # DEBUG: Log the actual model_provider being used
    logger.info(f"Chat request - Message: {message[:50]}...")
    logger.info(f"Chat request - Model Provider: {request.model_provider}")
    logger.info(f"Chat request - User ID: {user_id}")
    logger.info(f"Chat request - Full request: {request.model_dump()}")

    return StreamingResponse(
        create_streaming_response(
            message=message,
            conversation_history=request.conversation_history,
            session_id=session_id,
            user_id=user_id,  # Pass authenticated user_id
            model_provider=request.model_provider,
            response_style=request.response_style
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/stream")
async def chat_stream_get(
    session_id: str = Query(...),
    message: str = Query(...),
    model_provider: Optional[str] = Query("llamacpp-gpt-oss"),
    response_style: Optional[str] = Query("Normal"),
    web_search: Optional[bool] = Query(False)
):
    """
    Stream chat responses with real-time tool execution updates (GET for EventSource).

    Args:
        session_id: Session ID
        message: User message
        model_provider: Model provider to use
        response_style: Response style
        web_search: Enable web search

    Returns:
        StreamingResponse with Server-Sent Events (SSE)
    """
    logger.info(f"Chat request received (GET): {message[:50]}...")

    return StreamingResponse(
        create_streaming_response(
            message=message,
            conversation_history=[],  # EventSource doesn't send history
            session_id=session_id,
            model_provider=model_provider,
            response_style=response_style
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# Google ADK Endpoints (New multi-agent system with LiteLLM support)
# ============================================================================

@router.post("/chat/adk/stream")
async def chat_adk_stream_post(request: ChatStreamRequest, current_user: dict = Depends(get_current_user)):
    """
    Stream chat responses using Google ADK multi-agent system (POST).

    Supports multiple model providers via LiteLLM:
    - Default configured Gemini model (from GEMINI_MODEL_ID env var)
    - "openai/gpt-4o" (OpenAI via LiteLLM)
    - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
    - "ollama_chat/llama3.2" (Ollama via LiteLLM)

    Requires Firebase Authentication.
    """
    # Extract user_id from authenticated token
    user_id = get_user_id_from_token(current_user)

    # Handle both formats
    message = request.content if request.content else request.message
    session_id = request.session_id

    logger.info(f"[ADK] Chat request - Message: {message[:50]}...")
    logger.info(f"[ADK] Chat request - Model Provider: {request.model_provider}")
    logger.info(f"[ADK] Chat request - User ID: {user_id}")

    return StreamingResponse(
        create_adk_streaming_response(
            message=message,
            conversation_history=request.conversation_history,
            session_id=session_id,
            user_id=user_id,
            model_provider=request.model_provider,
            response_style=request.response_style
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/adk/stream")
async def chat_adk_stream_get(
    session_id: str = Query(...),
    message: str = Query(...),
    model_provider: Optional[str] = Query(Config.GEMINI_MODEL_ID),
    response_style: Optional[str] = Query("Normal"),
):
    """
    Stream chat responses using Google ADK multi-agent system (GET for EventSource).

    Supports multiple model providers via LiteLLM:
    - Default configured Gemini model (from GEMINI_MODEL_ID env var)
    - "openai/gpt-4o" (OpenAI via LiteLLM)
    - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
    - "ollama_chat/llama3.2" (Ollama via LiteLLM)
    """
    logger.info(f"[ADK] Chat request received (GET): {message[:50]}...")

    return StreamingResponse(
        create_adk_streaming_response(
            message=message,
            conversation_history=[],
            session_id=session_id,
            model_provider=model_provider,
            response_style=response_style
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/adk/providers")
async def get_adk_model_providers():
    """
    Get available model providers for ADK.
    
    Returns list of available providers with their status and available models.
    """
    providers = ADKModelProviderFactory.get_available_providers()
    default_provider = ADKModelProviderFactory.get_default_provider()
    default_model = ADKModelProviderFactory.get_default_model()
    
    return {
        "providers": providers,
        "default_provider": default_provider,
        "default_model": default_model
    }


# ============================================================================
# Test endpoint (no auth required) - REMOVE IN PRODUCTION
# ============================================================================

@router.post("/chat/adk/test")
async def chat_adk_test(request: ChatStreamRequest):
    """
    Test ADK streaming endpoint (NO AUTH REQUIRED - for development only).
    
    Remove this endpoint in production!
    """
    message = request.content if request.content else request.message
    session_id = request.session_id or "test-session"

    logger.info(f"[ADK-TEST] Message: {message[:50]}...")
    logger.info(f"[ADK-TEST] Model Provider: {request.model_provider}")

    return StreamingResponse(
        create_adk_streaming_response(
            message=message,
            conversation_history=request.conversation_history,
            session_id=session_id,
            user_id="test-user",
            model_provider=request.model_provider,
            response_style=request.response_style
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
