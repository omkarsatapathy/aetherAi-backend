"""Session CRUD endpoints."""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from src.api.models import SessionCreate, SessionUpdate
from src.database import DatabaseManager
from src.services.firestore_service import firestore_service
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger
import uuid

logger = get_logger("chatbot.routes.sessions")

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Database manager will be injected by the app (kept for backward compatibility)
_db_manager: Optional[DatabaseManager] = None


def set_db_manager(db_manager: DatabaseManager):
    """Inject database manager instance."""
    global _db_manager
    _db_manager = db_manager


@router.post("")
async def create_session(
    request: SessionCreate,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new chat session.

    Args:
        request: SessionCreate containing session title
        http_request: HTTP request object
        current_user: Authenticated user from token

    Returns:
        Created session information
    """
    user_id = get_user_id_from_token(current_user)
    session_id = str(uuid.uuid4())

    logger.info(f"Creating session: {session_id} for user {user_id} with title: {request.title}")

    try:
        session = await firestore_service.create_session(user_id, session_id, request.title)
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("")
async def list_sessions(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    List all chat sessions ordered by last updated.

    Args:
        limit: Maximum number of sessions to return
        current_user: Authenticated user from token

    Returns:
        List of sessions
    """
    user_id = get_user_id_from_token(current_user)

    try:
        sessions = await firestore_service.list_sessions(user_id, limit=limit)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    include_messages: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific session by ID.

    Args:
        session_id: Session identifier
        include_messages: Whether to include messages in response
        current_user: Authenticated user from token

    Returns:
        Session information with optional messages
    """
    user_id = get_user_id_from_token(current_user)

    try:
        session = await firestore_service.get_session(user_id, session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if include_messages:
            messages = await firestore_service.get_messages(user_id, session_id)
            session['messages'] = messages

        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: SessionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update session title.

    Args:
        session_id: Session identifier
        request: SessionUpdate containing new title
        current_user: Authenticated user from token

    Returns:
        Success status
    """
    user_id = get_user_id_from_token(current_user)

    logger.info(f"Updating session {session_id} with title: {request.title}")

    try:
        # Use force=True for manual user edits via API
        success = await firestore_service.update_session_title(user_id, session_id, request.title, force=True)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Session updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a session and all its messages.

    Args:
        session_id: Session identifier
        current_user: Authenticated user from token

    Returns:
        Success status
    """
    user_id = get_user_id_from_token(current_user)

    logger.info(f"Deleting session: {session_id}")

    try:
        # Delete from Firestore
        success = await firestore_service.delete_session(user_id, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete files from Cloud Storage
        from src.services.storage_service import storage_service
        await storage_service.delete_session_files(user_id, session_id)

        return {"success": True, "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
