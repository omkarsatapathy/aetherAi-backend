"""Gmail OAuth authentication routes - Multi-tenant secure version."""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from .auth_manager import GmailAuthManager
from ..middleware.auth_middleware import get_current_user, get_user_id_from_token
from ..logging_config import get_logger

logger = get_logger("chatbot.gmail.routes")

router = APIRouter(prefix="/api/auth/gmail", tags=["Gmail Authentication"])


class AuthStatusResponse(BaseModel):
    """Response model for auth status."""
    authenticated: bool
    user_id: str
    message: str
    metadata: Optional[dict] = None


@router.get("/authorize")
async def authorize_gmail(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Initiate Gmail OAuth authorization flow.

    SECURITY: Requires Firebase Authentication.
    User must be logged in to authorize Gmail access.

    Args:
        request: FastAPI request object
        current_user: Decoded Firebase Auth token (from middleware)

    Returns:
        Redirect to Google OAuth consent screen
    """
    try:
        user_id = get_user_id_from_token(current_user)

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        auth_manager = GmailAuthManager()

        # Build redirect URI (Cloud Run URL)
        # In production, this should be your actual domain
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/auth/gmail/callback"

        # Get authorization URL with user_id as state
        auth_url = auth_manager.get_authorization_url(user_id, redirect_uri)

        logger.info(
            "Gmail authorization initiated",
            extra={"extra_data": {"user_id": user_id, "redirect_uri": redirect_uri}}
        )

        return RedirectResponse(url=auth_url)

    except FileNotFoundError as e:
        logger.error(f"OAuth client config not found: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Gmail OAuth configuration not found. Please contact administrator."
        )
    except Exception as e:
        logger.error(f"Failed to initiate authorization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")


@router.get("/callback")
async def gmail_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None, state: Optional[str] = None):
    """
    Handle OAuth callback from Google.

    SECURITY: The state parameter contains the user_id for verification.
    This prevents CSRF attacks and ensures the callback is for the correct user.

    Args:
        request: FastAPI request object
        code: Authorization code from Google
        error: Error message if authorization failed
        state: User ID passed as state parameter

    Returns:
        Success or error response
    """
    if error:
        logger.error(f"OAuth authorization failed: {error}")
        return HTMLResponse(content=_generate_error_html(error), status_code=400)

    if not code:
        logger.error("No authorization code received")
        return HTMLResponse(content=_generate_error_html("No authorization code received"), status_code=400)

    if not state:
        logger.error("No state parameter received (user_id missing)")
        return HTMLResponse(content=_generate_error_html("Invalid callback - missing state"), status_code=400)

    try:
        user_id = state  # user_id was passed as state parameter

        auth_manager = GmailAuthManager()

        # Build redirect URI (must match the one used in authorization)
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/auth/gmail/callback"

        # Exchange code for credentials and save to Firestore
        credentials = auth_manager.exchange_code(user_id, code, redirect_uri)

        logger.info(
            "Gmail authorization successful",
            extra={"extra_data": {"user_id": user_id}}
        )

        # Return success HTML
        return HTMLResponse(content=_generate_success_html())

    except Exception as e:
        logger.error(f"Failed to exchange authorization code: {str(e)}", exc_info=True)
        return HTMLResponse(content=_generate_error_html(str(e)), status_code=500)


@router.get("/status", response_model=AuthStatusResponse)
async def gmail_auth_status(current_user: dict = Depends(get_current_user)):
    """
    Check Gmail authentication status for current user.

    SECURITY: Requires Firebase Authentication.
    Returns status only for the authenticated user.

    Args:
        current_user: Decoded Firebase Auth token (from middleware)

    Returns:
        Authentication status
    """
    try:
        user_id = get_user_id_from_token(current_user)

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        auth_manager = GmailAuthManager()
        status = auth_manager.get_auth_status(user_id)

        logger.info(
            "Gmail auth status checked",
            extra={"extra_data": {"user_id": user_id, "authenticated": status['authenticated']}}
        )

        return AuthStatusResponse(**status)

    except Exception as e:
        logger.error(f"Failed to check auth status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/revoke")
async def revoke_gmail_auth(current_user: dict = Depends(get_current_user)):
    """
    Revoke Gmail authentication for current user.

    SECURITY: Requires Firebase Authentication.
    Only revokes access for the authenticated user.

    Args:
        current_user: Decoded Firebase Auth token (from middleware)

    Returns:
        Success message
    """
    try:
        user_id = get_user_id_from_token(current_user)

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        auth_manager = GmailAuthManager()
        success = auth_manager.revoke_access(user_id)

        if success:
            logger.info(
                "Gmail auth revoked",
                extra={"extra_data": {"user_id": user_id}}
            )
            return {"success": True, "message": "Gmail authentication revoked successfully"}
        else:
            return {"success": False, "message": "No active authentication found"}

    except Exception as e:
        logger.error(f"Failed to revoke auth: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Revoke failed: {str(e)}")


def _generate_success_html() -> str:
    """Generate success page HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gmail Authorization Successful</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }
            h1 { color: #4CAF50; margin-bottom: 20px; }
            p { color: #666; font-size: 16px; line-height: 1.6; }
            .success-icon { font-size: 64px; margin-bottom: 20px; }
            .button {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }
            .button:hover { background: #5568d3; }
        </style>
        <script>
            // Auto-close window after 3 seconds if opened as popup
            if (window.opener) {
                setTimeout(() => {
                    window.opener.postMessage({ type: 'gmail_auth_success' }, '*');
                    window.close();
                }, 3000);
            }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Authorization Successful!</h1>
            <p>Your Gmail account has been successfully connected to AetherAI.</p>
            <p>You can now use Gmail features in the chatbot.</p>
            <p><small>This window will close automatically...</small></p>
            <a href="/" class="button" onclick="window.close()">Close Window</a>
        </div>
    </body>
    </html>
    """


def _generate_error_html(error_message: str) -> str:
    """Generate error page HTML."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gmail Authorization Failed</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            h1 {{ color: #f5576c; margin-bottom: 20px; }}
            p {{ color: #666; font-size: 16px; line-height: 1.6; }}
            .error-icon {{ font-size: 64px; margin-bottom: 20px; }}
            .error-details {{
                background: #fff3cd;
                border: 1px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                color: #856404;
            }}
            .button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .button:hover {{ background: #5568d3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">❌</div>
            <h1>Authorization Failed</h1>
            <p>We couldn't connect your Gmail account.</p>
            <div class="error-details">
                <strong>Error:</strong> {error_message}
            </div>
            <p>Please try again or contact support if the problem persists.</p>
            <a href="/" class="button" onclick="window.close()">Close Window</a>
        </div>
    </body>
    </html>
    """
