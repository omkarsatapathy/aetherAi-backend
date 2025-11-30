"""Gmail OAuth authentication manager for multi-tenant Cloud Run environment."""
import os
import json
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from .credentials_manager import GmailCredentialsManager
from ..config import Config
from ..logging_config import get_logger

logger = get_logger("chatbot.gmail.auth_manager")

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailAuthManager:
    """Manages Gmail OAuth authentication for multi-tenant environment."""

    def __init__(self):
        """Initialize Gmail auth manager."""
        self.credentials_manager = GmailCredentialsManager()

        # Get OAuth client config from environment variable or Secret Manager
        # In production, store credentials.json in Google Secret Manager
        self.client_config = self._get_client_config()

    def _get_client_config(self) -> dict:
        """
        Get OAuth client configuration.

        Priority:
        1. GOOGLE_OAUTH_CLIENT_CONFIG environment variable (JSON string)
        2. GOOGLE_OAUTH_CLIENT_CONFIG_PATH file path
        3. credentials.json in gmail_credentials directory (legacy)

        Returns:
            OAuth client configuration dict
        """
        # Option 1: Environment variable with JSON
        config_json = os.getenv('GOOGLE_OAUTH_CLIENT_CONFIG')
        if config_json:
            try:
                logger.info("Loading OAuth config from GOOGLE_OAUTH_CLIENT_CONFIG env var")
                return json.loads(config_json)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_OAUTH_CLIENT_CONFIG: {e}")

        # Option 2: File path from environment
        config_path = os.getenv('GOOGLE_OAUTH_CLIENT_CONFIG_PATH')
        if config_path and os.path.exists(config_path):
            try:
                logger.info(f"Loading OAuth config from file: {config_path}")
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load OAuth config from {config_path}: {e}")

        # Option 3: Legacy path (for backward compatibility)
        legacy_path = os.path.join(Config.GMAIL_CREDENTIALS_DIR, "credentials.json")
        if os.path.exists(legacy_path):
            try:
                logger.warning(f"Using legacy credentials.json from {legacy_path}")
                with open(legacy_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load legacy credentials: {e}")

        raise FileNotFoundError(
            "Google OAuth client configuration not found. Set GOOGLE_OAUTH_CLIENT_CONFIG "
            "or GOOGLE_OAUTH_CLIENT_CONFIG_PATH environment variable."
        )

    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """
        Generate OAuth authorization URL for user.

        Args:
            user_id: Firebase Auth user ID
            redirect_uri: OAuth callback URL

        Returns:
            Authorization URL to redirect user to
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )

            # Use user_id as state parameter for security
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=user_id  # Pass user_id as state for verification in callback
            )

            logger.info(f"Generated auth URL for user: {user_id}")
            return auth_url

        except Exception as e:
            logger.error(f"Failed to generate auth URL for user {user_id}: {str(e)}", exc_info=True)
            raise

    def exchange_code(self, user_id: str, code: str, redirect_uri: str) -> Credentials:
        """
        Exchange authorization code for OAuth credentials.

        Args:
            user_id: Firebase Auth user ID
            code: Authorization code from OAuth callback
            redirect_uri: OAuth callback URL (must match the one used in authorization)

        Returns:
            OAuth credentials

        Raises:
            Exception if exchange fails
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )

            # Exchange code for token
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Save encrypted credentials to Firestore
            self.credentials_manager.save_credentials(user_id, credentials)

            logger.info(f"Successfully exchanged code and saved credentials for user: {user_id}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to exchange code for user {user_id}: {str(e)}", exc_info=True)
            raise

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get valid credentials for user, refreshing if necessary.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            Valid OAuth credentials or None if not authenticated
        """
        try:
            credentials = self.credentials_manager.get_credentials(user_id)

            if not credentials:
                return None

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                logger.info(f"Refreshing expired credentials for user: {user_id}")
                credentials = self.credentials_manager.refresh_credentials(user_id)

            return credentials

        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}: {str(e)}", exc_info=True)
            return None

    def is_authenticated(self, user_id: str) -> bool:
        """
        Check if user has valid Gmail authentication.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            True if user is authenticated, False otherwise
        """
        return self.credentials_manager.is_authenticated(user_id)

    def revoke_access(self, user_id: str) -> bool:
        """
        Revoke Gmail access for user.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Optionally revoke with Google (requires additional API call)
            # For now, just delete from our storage
            success = self.credentials_manager.delete_credentials(user_id)

            if success:
                logger.info(f"Revoked Gmail access for user: {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to revoke access for user {user_id}: {str(e)}", exc_info=True)
            return False

    def get_auth_status(self, user_id: str) -> dict:
        """
        Get detailed authentication status for user.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            Dict with authentication status and metadata
        """
        try:
            is_authenticated = self.is_authenticated(user_id)
            metadata = self.credentials_manager.get_auth_metadata(user_id) if is_authenticated else None

            return {
                'authenticated': is_authenticated,
                'user_id': user_id,
                'metadata': metadata,
                'message': 'Authenticated' if is_authenticated else 'Not authenticated'
            }

        except Exception as e:
            logger.error(f"Failed to get auth status for user {user_id}: {str(e)}", exc_info=True)
            return {
                'authenticated': False,
                'user_id': user_id,
                'error': str(e),
                'message': 'Error checking authentication status'
            }
