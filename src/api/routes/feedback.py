"""User feedback endpoint for collecting app feedback."""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from src.services.firestore_service import firestore_service
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.feedback")

router = APIRouter(prefix="/api", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    is_positive: bool  # True for positive feedback, False for negative


@router.get("/feedback/test")
async def test_feedback_route():
    """Test endpoint to verify feedback routes are working."""
    return {
        "status": "ok",
        "message": "Feedback routes are registered and working",
        "endpoint": "/api/feedback"
    }


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit user feedback to update their feedback score.
    
    Positive feedback: +10 points
    Negative feedback: -10 points

    This endpoint:
    - Requires Firebase authentication
    - Updates the user's feedback_score in Firestore
    - Score can range from -infinity to +infinity

    Args:
        request: FeedbackRequest with is_positive boolean
        current_user: Authenticated user from Firebase token

    Returns:
        Updated feedback score

    Raises:
        HTTPException 500: On server error
    """
    # Log incoming request
    print(f"\n[FEEDBACK ENDPOINT] Received request")
    print(f"[FEEDBACK ENDPOINT] Request object: {request}")
    print(f"[FEEDBACK ENDPOINT] is_positive value: {request.is_positive}")
    print(f"[FEEDBACK ENDPOINT] Request dict: {request.model_dump()}\n")
    
    # Extract user_id from authenticated token
    user_id = get_user_id_from_token(current_user)
    
    feedback_type = "positive" if request.is_positive else "negative"
    logger.info(f"📝 Received {feedback_type} feedback from user: {user_id}")
    print(f"[FEEDBACK ENDPOINT] User ID: {user_id}, Feedback type: {feedback_type}")

    try:
        # Update feedback score in Firestore
        result = await firestore_service.update_feedback_score(user_id, request.is_positive)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update feedback score"
            )

        return {
            "success": True,
            "message": f"{feedback_type.capitalize()} feedback recorded",
            "feedback_score": result['feedback_score']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/user/cost")
async def get_user_cost_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's cost tracking data and feedback score.
    
    This endpoint:
    - Requires Firebase authentication
    - Returns total cost in INR and USD
    - Returns total tokens used
    - Returns feedback_score
    - Returns billing cycle information

    Args:
        current_user: Authenticated user from Firebase token

    Returns:
        Cost tracking data and feedback score

    Raises:
        HTTPException 404: If user data not found
        HTTPException 500: On server error
    """
    # Extract user_id from authenticated token
    user_id = get_user_id_from_token(current_user)
    
    logger.info(f"📊 Fetching cost and feedback data for user: {user_id}")

    try:
        # Get user cost data (includes feedback_score)
        cost_data = await firestore_service.get_user_cost(user_id)
        
        if cost_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User cost data not found"
            )

        return {
            "success": True,
            "data": cost_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user cost info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user cost info: {str(e)}"
        )
