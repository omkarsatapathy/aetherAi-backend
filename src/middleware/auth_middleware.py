"""Authentication Middleware for FastAPI."""
from fastapi import Request, HTTPException, status
from typing import Optional
from src.firebase_admin_config import verify_token
from src.logging_config import get_logger

logger = get_logger("chatbot.middleware.auth")


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and verify Firebase ID token from request.

    Args:
        request: FastAPI request object

    Returns:
        Decoded token with user information or None

    Raises:
        HTTPException: If token is invalid or missing
    """
    # Get Authorization header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        logger.warning("No Authorization header found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    try:
        scheme, token = auth_header.split()

        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token with Firebase
        decoded_token = await verify_token(token)

        return decoded_token

    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Extract and verify Firebase ID token from request (optional).

    Returns None if no token is provided instead of raising an exception.

    Args:
        request: FastAPI request object

    Returns:
        Decoded token with user information or None
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def get_user_id_from_token(decoded_token: dict) -> str:
    """
    Extract user ID from decoded token.

    Args:
        decoded_token: Decoded Firebase token

    Returns:
        User ID (UID)
    """
    return decoded_token.get('uid')


def get_user_email_from_token(decoded_token: dict) -> Optional[str]:
    """
    Extract user email from decoded token.

    Args:
        decoded_token: Decoded Firebase token

    Returns:
        User email or None
    """
    return decoded_token.get('email')
