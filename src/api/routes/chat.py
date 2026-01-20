"""Chat streaming endpoint - Google ADK only."""
import json
from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from src.api.models import ChatRequest, LocationSubmitRequest
from src.agent.google_adk import create_adk_streaming_response, ADKModelProviderFactory
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger
from src.config import Config
from src.tools.google_maps import set_user_location
from src.services.firestore_service import firestore_service
from typing import Optional, List, Dict, Any, AsyncGenerator
from pydantic import BaseModel

logger = get_logger("chatbot.routes.chat")

router = APIRouter(prefix="/api", tags=["chat"])


async def balance_exceeded_stream(balance_info: Dict) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response when user has exceeded their balance limit.
    """
    error_message = balance_info.get("message", "Monthly limit exceeded. Please recharge to continue.")
    error_data = {
        "type": "balance_exceeded",
        "message": error_message,
        "total_cost_inr": balance_info.get("total_cost_inr", 0),
        "limit_inr": balance_info.get("limit_inr", 100),
        "remaining_balance": balance_info.get("remaining_balance", 0)
    }
    yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    yield "data: [DONE]\n\n"


# Preference response model for shopping workflow
class PreferenceResponse(BaseModel):
    """Single preference question response."""
    question: str
    options_available: List[str]
    options_selected: Any  # Can be string or List[str] for multi-select


# Add/update the request model to match what Swagger expects
class ChatStreamRequest(BaseModel):
    """Request model for chat streaming that matches frontend payload."""
    message: str = ""  # Optional when responses provided
    session_id: Optional[str] = None
    model_provider: Optional[str] = Config.GEMINI_MODEL_ID
    response_style: Optional[str] = "Normal"
    web_search: bool = False
    conversation_history: List[Dict[str, Any]] = []
    tool: Optional[str] = None  # Explicit tool routing: 'shopping_assist', etc.

    # Shopping preference responses (Phase 2 trigger)
    responses: Optional[List[PreferenceResponse]] = None

    # Alternative fields for direct message object (from frontend)
    id: Optional[int] = None
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/chat/stream")
async def chat_stream_post(request: ChatStreamRequest, current_user: dict = Depends(get_current_user)):
    """
    Stream chat responses using Google ADK (POST).
    Requires Firebase Authentication.

    Supports multiple model providers via LiteLLM:
    - Default configured Gemini model (from GEMINI_MODEL_ID env var)
    - "openai/gpt-4o" (OpenAI via LiteLLM)
    - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
    - "ollama_chat/llama3.2" (Ollama via LiteLLM)
    """
    # Extract user_id from authenticated token
    user_id = get_user_id_from_token(current_user)

    # Check user balance before processing request
    balance_info = await firestore_service.check_user_balance(user_id)
    if not balance_info.get("has_balance", True):
        logger.warning(f"[ADK] User {user_id} has exceeded monthly limit: ₹{balance_info.get('total_cost_inr', 0):.2f}")
        return StreamingResponse(
            balance_exceeded_stream(balance_info),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Handle both formats
    message = request.content if request.content else request.message
    session_id = request.session_id

    logger.info(f"[ADK] Chat request - Message: {message[:50] if message else 'Preference responses'}...")
    logger.info(f"[ADK] Chat request - Model Provider: {request.model_provider}")
    logger.info(f"[ADK] Chat request - User ID: {user_id}")
    if request.tool:
        logger.info(f"[ADK] Chat request - Tool: {request.tool}")
    if request.responses:
        logger.info(f"[ADK] Chat request - Preference Responses: {len(request.responses)} answers")

    # Print conversation history before sending to Agent
    print(f"\n[CHAT HISTORY] Sending to Agent - History: {request.conversation_history}\n")

    return StreamingResponse(
        create_adk_streaming_response(
            message=message,
            conversation_history=request.conversation_history,
            session_id=session_id,
            user_id=user_id,
            model_provider=request.model_provider,
            response_style=request.response_style,
            tool=request.tool,
            preference_responses=request.responses
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
    model_provider: Optional[str] = Query(Config.GEMINI_MODEL_ID),
    response_style: Optional[str] = Query("Normal"),
):
    """
    Stream chat responses using Google ADK (GET for EventSource).

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


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/chat/providers")
async def get_model_providers():
    """
    Get available model providers.

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
# Location Endpoint
# ============================================================================

@router.post("/chat/location")
async def submit_user_location(
    request: LocationSubmitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Receive and store user location coordinates for map-based tools.

    This endpoint is called by the frontend after the user grants location permission.
    The location is stored in session and used by all subsequent map tool invocations.
    """
    user_id = get_user_id_from_token(current_user)

    logger.info(f"[Location] Received location for session {request.session_id}: ({request.latitude}, {request.longitude})")

    # Validate coordinates
    if not (-90 <= request.latitude <= 90):
        logger.warning(f"[Location] Invalid latitude: {request.latitude}")
        return {"status": "error", "message": "Invalid latitude (must be between -90 and 90)"}

    if not (-180 <= request.longitude <= 180):
        logger.warning(f"[Location] Invalid longitude: {request.longitude}")
        return {"status": "error", "message": "Invalid longitude (must be between -180 and 180)"}

    # Store location in session
    set_user_location(
        session_id=request.session_id,
        latitude=request.latitude,
        longitude=request.longitude
    )

    logger.info(f"[Location] Successfully stored location for session {request.session_id}")

    return {
        "status": "success",
        "message": "Location saved successfully",
        "session_id": request.session_id
    }


# ============================================================================
# Test endpoint (no auth required) - REMOVE IN PRODUCTION
# ============================================================================

@router.post("/chat/test")
async def chat_test(request: ChatStreamRequest):
    """
    Test streaming endpoint (NO AUTH REQUIRED - for development only).

    Remove this endpoint in production!
    """
    message = request.content if request.content else request.message
    session_id = request.session_id or "test-session"

    logger.info(f"[TEST] Message: {message[:50] if message else 'Preference responses'}...")
    logger.info(f"[TEST] Model Provider: {request.model_provider}")
    if request.tool:
        logger.info(f"[TEST] Tool: {request.tool}")
    if request.responses:
        logger.info(f"[TEST] Preference Responses: {len(request.responses)} answers")

    # Print conversation history before sending to Agent
    print(f"\n[CHAT HISTORY]: \n\n Sending to Agent - History: {request.conversation_history}\n")

    return StreamingResponse(
        create_adk_streaming_response(
            message=message,
            conversation_history=request.conversation_history,
            session_id=session_id,
            user_id="test-user",
            model_provider=request.model_provider,
            response_style=request.response_style,
            tool=request.tool,
            preference_responses=request.responses
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
