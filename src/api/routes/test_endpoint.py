"""Simple test POST endpoint."""
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/test", tags=["Test"])


class TestRequest(BaseModel):
    """Simple test request model."""
    message: str
    session_id: Optional[str] = None


class TestResponse(BaseModel):
    """Simple test response model."""
    success: bool
    echo_message: str
    session_id: Optional[str]
    timestamp: str


@router.post("/echo", response_model=TestResponse)
async def test_echo(request: TestRequest):
    """
    Simple POST endpoint that echoes back your message.
    
    Example:
    {
        "message": "Hi there",
        "session_id": "optional-session-id"
    }
    """
    return TestResponse(
        success=True,
        echo_message=f"You said: {request.message}",
        session_id=request.session_id,
        timestamp=datetime.now().isoformat()
    )
