"""Simple chat POST endpoint without streaming."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/chat", tags=["chat"])


class SimpleChatRequest(BaseModel):
    """Simple chat request model."""
    message: str
    session_id: Optional[str] = None
    model_provider: Optional[str] = "openai"


class SimpleChatResponse(BaseModel):
    """Simple chat response model."""
    id: int
    session_id: str
    role: str
    content: str
    timestamp: str


@router.post("/simple", response_model=SimpleChatResponse)
async def chat_simple(request: SimpleChatRequest):
    """
    Simple POST endpoint for chat (non-streaming).
    
    Request:
    {
        "message": "Hi there",
        "session_id": "8a30ae24-9630-4b06-a48e-713fd5714081"
    }
    
    Response:
    {
        "id": 8,
        "session_id": "8a30ae24-9630-4b06-a48e-713fd5714081",
        "role": "assistant",
        "content": "Hello! How can I help you?",
        "timestamp": "2025-11-27T09:15:00.123456"
    }
    """
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Simple echo response (replace with actual AI logic)
    response_content = f"You said: {request.message}"
    
    return SimpleChatResponse(
        id=999,  # Replace with actual DB ID
        session_id=session_id,
        role="assistant",
        content=response_content,
        timestamp=datetime.now().isoformat()
    )
