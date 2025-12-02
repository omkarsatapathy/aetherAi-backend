"""Message endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from src.api.models import MessageCreate
from src.database import DatabaseManager
from src.services.firestore_service import firestore_service
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.messages")

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Database manager will be injected by the app (kept for backward compatibility)
_db_manager: Optional[DatabaseManager] = None


def set_db_manager(db_manager: DatabaseManager):
    """Inject database manager instance."""
    global _db_manager
    _db_manager = db_manager


@router.post("")
async def create_message(
    request: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a message to a session (now using Firestore).

    Args:
        request: MessageCreate containing session_id, role, and content
        current_user: Authenticated user from token

    Returns:
        Created message information
    """
    user_id = get_user_id_from_token(current_user)

    logger.info(f"Adding message to session {request.session_id}: {request.role} (user: {user_id})")

    try:
        # Verify session exists
        session = await firestore_service.get_session(user_id, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Add message to Firestore
        message = await firestore_service.add_message(
            user_id=user_id,
            session_id=request.session_id,
            role=request.role,
            content=request.content
        )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")


@router.get("/{session_id}")
async def get_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all messages for a session (now using Firestore).

    Args:
        session_id: Session identifier
        current_user: Authenticated user from token

    Returns:
        List of messages
    """
    user_id = get_user_id_from_token(current_user)

    try:
        # Verify session exists
        session = await firestore_service.get_session(user_id, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get messages from Firestore
        messages = await firestore_service.get_messages(user_id, session_id)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
