"""Firebase Admin SDK Configuration and Initialization."""
import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from src.logging_config import get_logger

logger = get_logger("chatbot.firebase_admin")

# Global Firebase app instance
_firebase_app = None
_firestore_client = None
_storage_bucket = None


def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app, _firestore_client, _storage_bucket

    if _firebase_app is not None:
        logger.info("Firebase Admin SDK already initialized")
        return _firebase_app

    try:
        # Option 1: Use service account JSON file
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

        if service_account_path and os.path.exists(service_account_path):
            logger.info(f"Initializing Firebase with service account: {service_account_path}")
            cred = credentials.Certificate(service_account_path)

        # Option 2: Use service account JSON from environment variable
        elif os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'):
            logger.info("Initializing Firebase with service account from environment variable")
            service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'))
            cred = credentials.Certificate(service_account_info)

        # Option 3: Use Application Default Credentials (for GCP deployment)
        else:
            logger.info("Initializing Firebase with Application Default Credentials")
            cred = credentials.ApplicationDefault()

        # Initialize the app
        _firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': 'aetherai-c7218.appspot.com'
        })

        # Initialize Firestore client
        _firestore_client = firestore.client()

        # Initialize Storage bucket
        _storage_bucket = storage.bucket()

        logger.info("Firebase Admin SDK initialized successfully")
        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        # Don't raise - allow app to start without Firebase in development
        return None


def get_firestore_client():
    """Get Firestore client instance."""
    global _firestore_client

    if _firestore_client is None:
        initialize_firebase()

    return _firestore_client


def get_storage_bucket():
    """Get Storage bucket instance."""
    global _storage_bucket

    if _storage_bucket is None:
        initialize_firebase()

    return _storage_bucket


async def verify_token(id_token: str) -> dict:
    """
    Verify Firebase ID token and return decoded token.

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token containing user information

    Raises:
        ValueError: If token is invalid
    """
    try:
        # Log token info for debugging (not the full token for security)
        token_preview = f"{id_token[:20]}...{id_token[-10:]}" if len(id_token) > 30 else id_token
        logger.info(f"Verifying token (length={len(id_token)}, preview={token_preview})")
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)

        logger.info(f"Token verified for user: {decoded_token.get('uid')}")
        return decoded_token

    except auth.InvalidIdTokenError as e:
        logger.error(f"Invalid ID token: {str(e)}")
        raise ValueError("Invalid authentication token")

    except auth.ExpiredIdTokenError:
        logger.error("Expired ID token")
        raise ValueError("Authentication token has expired")

    except Exception as e:
        logger.error(f"Token verification error: {type(e).__name__}: {e}", exc_info=True)
        raise ValueError("Failed to verify authentication token")


async def get_user_by_uid(uid: str):
    """
    Get user record by UID.

    Args:
        uid: User ID

    Returns:
        UserRecord object
    """
    try:
        user = auth.get_user(uid)
        return user
    except Exception as e:
        logger.error(f"Error getting user {uid}: {e}", exc_info=True)
        return None


# Initialize Firebase on module import
initialize_firebase()
