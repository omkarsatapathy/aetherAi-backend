"""Secure Gmail credentials management using Firestore and encryption."""
import os
import json
from typing import Optional, Dict
from datetime import datetime
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from ..firebase_admin_config import get_firestore_client
from ..logging_config import get_logger

logger = get_logger("chatbot.gmail.credentials")


class GmailCredentialsManager:
    """Manages encrypted Gmail OAuth credentials in Firestore."""

    def __init__(self):
        """Initialize credentials manager."""
        self.db = get_firestore_client()

        # Get encryption key from environment or generate one
        encryption_key = os.getenv('GMAIL_TOKEN_ENCRYPTION_KEY')
        if not encryption_key:
            logger.warning("GMAIL_TOKEN_ENCRYPTION_KEY not set. Generating temporary key (not suitable for production)")
            encryption_key = Fernet.generate_key().decode()

        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def save_credentials(self, user_id: str, credentials: Credentials) -> bool:
        """
        Save encrypted OAuth credentials to Firestore.

        Args:
            user_id: Firebase Auth user ID
            credentials: Google OAuth credentials

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare credentials data
            creds_data = {
                'access_token': self._encrypt(credentials.token),
                'refresh_token': self._encrypt(credentials.refresh_token) if credentials.refresh_token else None,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': self._encrypt(credentials.client_secret) if credentials.client_secret else None,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                'updated_at': datetime.utcnow().isoformat(),
            }

            # Check if this is first time saving
            doc_ref = self.db.collection('users').document(user_id).collection('gmail_credentials').document('oauth')
            doc = doc_ref.get()

            if not doc.exists:
                creds_data['created_at'] = datetime.utcnow().isoformat()

            # Save to Firestore
            doc_ref.set(creds_data)

            logger.info(f"Gmail credentials saved for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save credentials for user {user_id}: {str(e)}", exc_info=True)
            return False

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Retrieve and decrypt OAuth credentials from Firestore.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            Google OAuth credentials or None if not found
        """
        try:
            # Retrieve from Firestore
            doc_ref = self.db.collection('users').document(user_id).collection('gmail_credentials').document('oauth')
            doc = doc_ref.get()

            if not doc.exists:
                logger.info(f"No Gmail credentials found for user: {user_id}")
                return None

            data = doc.to_dict()

            # Decrypt sensitive fields
            token = self._decrypt(data['access_token'])
            refresh_token = self._decrypt(data['refresh_token']) if data.get('refresh_token') else None
            client_secret = self._decrypt(data['client_secret']) if data.get('client_secret') else None

            # Reconstruct credentials object
            credentials = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri=data.get('token_uri'),
                client_id=data.get('client_id'),
                client_secret=client_secret,
                scopes=data.get('scopes'),
            )

            # Set expiry if available
            if data.get('expiry'):
                from datetime import datetime
                credentials.expiry = datetime.fromisoformat(data['expiry'])

            logger.info(f"Gmail credentials retrieved for user: {user_id}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to retrieve credentials for user {user_id}: {str(e)}", exc_info=True)
            return None

    def refresh_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Refresh expired credentials and save updated tokens.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            Refreshed credentials or None if refresh failed
        """
        try:
            credentials = self.get_credentials(user_id)

            if not credentials:
                logger.warning(f"No credentials to refresh for user: {user_id}")
                return None

            if not credentials.expired:
                logger.info(f"Credentials not expired for user: {user_id}")
                return credentials

            if not credentials.refresh_token:
                logger.error(f"No refresh token available for user: {user_id}")
                return None

            # Refresh the token
            from google.auth.transport.requests import Request
            credentials.refresh(Request())

            # Save updated credentials
            self.save_credentials(user_id, credentials)

            logger.info(f"Credentials refreshed for user: {user_id}")
            return credentials

        except Exception as e:
            logger.error(f"Failed to refresh credentials for user {user_id}: {str(e)}", exc_info=True)
            return None

    def delete_credentials(self, user_id: str) -> bool:
        """
        Delete user's Gmail credentials (revoke access).

        Args:
            user_id: Firebase Auth user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection('users').document(user_id).collection('gmail_credentials').document('oauth')
            doc_ref.delete()

            logger.info(f"Gmail credentials deleted for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete credentials for user {user_id}: {str(e)}", exc_info=True)
            return False

    def is_authenticated(self, user_id: str) -> bool:
        """
        Check if user has valid Gmail authentication.

        Args:
            user_id: Firebase Auth user ID

        Returns:
            True if authenticated with valid credentials, False otherwise
        """
        try:
            credentials = self.get_credentials(user_id)

            if not credentials:
                return False

            # Check if expired and can be refreshed
            if credentials.expired and credentials.refresh_token:
                credentials = self.refresh_credentials(user_id)
                return credentials is not None

            return credentials.valid

        except Exception as e:
            logger.error(f"Failed to check auth status for user {user_id}: {str(e)}", exc_info=True)
            return False

    def get_auth_metadata(self, user_id: str) -> Optional[Dict]:
        """
        Get metadata about user's Gmail authentication (without sensitive data).

        Args:
            user_id: Firebase Auth user ID

        Returns:
            Dict with auth metadata or None
        """
        try:
            doc_ref = self.db.collection('users').document(user_id).collection('gmail_credentials').document('oauth')
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()

            return {
                'scopes': data.get('scopes', []),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'has_refresh_token': data.get('refresh_token') is not None,
            }

        except Exception as e:
            logger.error(f"Failed to get auth metadata for user {user_id}: {str(e)}", exc_info=True)
            return None
