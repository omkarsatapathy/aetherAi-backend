"""Chat streaming endpoint."""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from src.api.models import ChatRequest
from src.agent.streaming_agent import create_streaming_response
from src.logging_config import get_logger
from typing import Optional

logger = get_logger("chatbot.routes.chat")

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/stream")
async def chat_stream_post(request: ChatRequest):
    """
    Stream chat responses with real-time tool execution updates (POST).

    Args:
        request: ChatRequest containing message, conversation history, and optional session_id

    Returns:
        StreamingResponse with Server-Sent Events (SSE)
    """
    logger.info(f"Chat request received (POST): {request.message[:50]}...")

    return StreamingResponse(
        create_streaming_response(
            message=request.message,
            conversation_history=request.conversation_history,
            session_id=request.session_id,
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
