"""User persona info endpoint for first-time users."""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List
from src.services.firestore_service import firestore_service
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.user_info")

router = APIRouter(prefix="/api", tags=["user-info"])


class UserInfoRequest(BaseModel):
    """Request model for user persona info collected at signup."""
    userId: str
    country: str
    ageGroup: str
    gender: str
    ethnicities: List[str]
    timestamp: str


@router.post("/info")
async def save_user_info(
    request: UserInfoRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Store user persona info for first-time users at signup.

    This endpoint:
    - Requires Firebase authentication
    - Validates that userId in payload matches authenticated user's UID
    - Returns 409 Conflict if persona already exists (one-time only)
    - Creates the user document in Firestore with persona data

    Args:
        request: UserInfoRequest containing persona data
        current_user: Authenticated user from Firebase token

    Returns:
        Created persona data with success message

    Raises:
        HTTPException 403: If userId doesn't match authenticated user
        HTTPException 409: If persona already exists for this user
        HTTPException 500: On server error
    """
    # Extract user_id from authenticated token
    token_user_id = get_user_id_from_token(current_user)

    # Validate that payload userId matches authenticated user
    if request.userId != token_user_id:
        logger.warning(f"User ID mismatch: payload={request.userId}, token={token_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in payload does not match authenticated user"
        )

    logger.info(f"📋 Saving persona for first-time user: {token_user_id}")

    try:
        # Prepare persona data (exclude userId and timestamp from stored data)
        persona_data = {
            'country': request.country,
            'ageGroup': request.ageGroup,
            'gender': request.gender,
            'ethnicities': request.ethnicities
        }

        # Save to Firestore
        saved_persona = await firestore_service.save_user_persona(token_user_id, persona_data)

        return {
            "success": True,
            "message": "User persona saved successfully",
            "persona": saved_persona
        }

    except ValueError as e:
        # Persona already exists
        logger.warning(f"Persona already exists for user {token_user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User persona already exists. This is a one-time operation."
        )
    except Exception as e:
        logger.error(f"Failed to save user persona: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save user persona: {str(e)}"
        )
