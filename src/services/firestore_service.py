"""Firestore Service for managing user data, sessions, and messages."""
from typing import List, Dict, Optional
from datetime import datetime
from google.cloud import firestore
from src.firebase_admin_config import get_firestore_client
from src.logging_config import get_logger

logger = get_logger("chatbot.services.firestore")


class FirestoreService:
    """Service for Firestore database operations."""

    def __init__(self):
        self.db = get_firestore_client()

    # ==================== USER MANAGEMENT ====================

    async def create_or_update_user(self, user_id: str, user_data: dict) -> dict:
        """
        Create or update user profile.

        Args:
            user_id: Firebase UID
            user_data: User profile data

        Returns:
            Updated user data
        """
        try:
            user_ref = self.db.collection('users').document(user_id)

            # Add timestamps
            user_data['updatedAt'] = firestore.SERVER_TIMESTAMP

            # Set or merge
            user_ref.set(user_data, merge=True)

            logger.info(f"User profile updated: {user_id}")
            return user_data

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
            raise

    async def get_user(self, user_id: str) -> Optional[dict]:
        """
        Get user profile.

        Args:
            user_id: Firebase UID

        Returns:
            User data or None
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            doc = user_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
            return None

    # ==================== SESSION MANAGEMENT ====================

    async def create_session(self, user_id: str, session_id: str, title: str) -> dict:
        """
        Create a new chat session.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            title: Session title

        Returns:
            Created session data
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            session_data = {
                'sessionId': session_id,
                'title': title,
                'hasDocuments': False,
                'vectorDbPath': None,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }

            session_ref.set(session_data)

            logger.info(f"Session created: {session_id} for user {user_id}")
            return session_data

        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            raise

    async def get_session(self, user_id: str, session_id: str) -> Optional[dict]:
        """
        Get a specific session.

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            Session data or None
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)
            doc = session_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
            return None

    async def list_sessions(self, user_id: str, limit: int = 50) -> List[dict]:
        """
        List all sessions for a user.

        Args:
            user_id: Firebase UID
            limit: Maximum number of sessions to return

        Returns:
            List of sessions
        """
        try:
            sessions_ref = self.db.collection('users').document(user_id).collection('sessions')
            query = sessions_ref.order_by('updatedAt', direction=firestore.Query.DESCENDING).limit(limit)

            docs = query.stream()
            sessions = [doc.to_dict() for doc in docs]

            logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions

        except Exception as e:
            logger.error(f"Error listing sessions: {e}", exc_info=True)
            return []

    async def update_session_title(self, user_id: str, session_id: str, title: str) -> bool:
        """
        Update session title.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            title: New title

        Returns:
            Success status
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            session_ref.update({
                'title': title,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })

            logger.info(f"Session {session_id} title updated")
            return True

        except Exception as e:
            logger.error(f"Error updating session title: {e}", exc_info=True)
            return False

    async def update_session_timestamp(self, user_id: str, session_id: str) -> bool:
        """
        Update session timestamp (when new message is added).

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            Success status
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            session_ref.update({
                'updatedAt': firestore.SERVER_TIMESTAMP
            })

            return True

        except Exception as e:
            logger.error(f"Error updating session timestamp: {e}", exc_info=True)
            return False

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a session and all its messages.

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            Success status
        """
        try:
            # Delete session document
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            # Delete all messages in the session
            messages_ref = session_ref.collection('messages')
            messages = messages_ref.stream()

            batch = self.db.batch()
            count = 0

            for msg in messages:
                batch.delete(msg.reference)
                count += 1

                # Firestore batch limit is 500
                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0

            # Delete all documents in the session
            documents_ref = session_ref.collection('documents')
            documents = documents_ref.stream()

            for doc in documents:
                batch.delete(doc.reference)
                count += 1

                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0

            # Delete session itself
            batch.delete(session_ref)
            batch.commit()

            logger.info(f"Session {session_id} deleted")
            return True

        except Exception as e:
            logger.error(f"Error deleting session: {e}", exc_info=True)
            return False

    # ==================== MESSAGE MANAGEMENT ====================

    async def add_message(self, user_id: str, session_id: str, role: str, content: str, audio_ref: Optional[str] = None) -> dict:
        """
        Add a message to a session.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            role: Message role (user/assistant)
            content: Message content
            audio_ref: Optional audio file reference

        Returns:
            Created message data
        """
        try:
            messages_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id).collection('messages')

            message_data = {
                'role': role,
                'content': content,
                'audioFileRef': audio_ref,
                'timestamp': firestore.SERVER_TIMESTAMP
            }

            # Add message
            doc_ref = messages_ref.add(message_data)
            message_data['messageId'] = doc_ref[1].id

            # Update session timestamp
            await self.update_session_timestamp(user_id, session_id)

            logger.info(f"Message added to session {session_id}")
            return message_data

        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            raise

    async def get_messages(self, user_id: str, session_id: str) -> List[dict]:
        """
        Get all messages for a session.

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            List of messages
        """
        try:
            messages_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id).collection('messages')
            query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING)

            docs = query.stream()
            messages = []

            for doc in docs:
                msg_data = doc.to_dict()
                msg_data['messageId'] = doc.id
                messages.append(msg_data)

            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages

        except Exception as e:
            logger.error(f"Error getting messages: {e}", exc_info=True)
            return []

    # ==================== DOCUMENT MANAGEMENT ====================

    async def add_document(self, user_id: str, session_id: str, filename: str, file_ref: str, file_size: int, mime_type: str) -> dict:
        """
        Add a document reference to a session.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            filename: Original filename
            file_ref: Cloud Storage reference
            file_size: File size in bytes
            mime_type: MIME type

        Returns:
            Created document data
        """
        try:
            documents_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id).collection('documents')

            document_data = {
                'filename': filename,
                'fileRef': file_ref,
                'fileSize': file_size,
                'mimeType': mime_type,
                'uploadedAt': firestore.SERVER_TIMESTAMP
            }

            # Add document
            doc_ref = documents_ref.add(document_data)
            document_data['documentId'] = doc_ref[1].id

            # Update session
            await self.update_session_timestamp(user_id, session_id)

            logger.info(f"Document added to session {session_id}")
            return document_data

        except Exception as e:
            logger.error(f"Error adding document: {e}", exc_info=True)
            raise

    async def get_documents(self, user_id: str, session_id: str) -> List[dict]:
        """
        Get all documents for a session.

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            List of documents
        """
        try:
            documents_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id).collection('documents')
            query = documents_ref.order_by('uploadedAt', direction=firestore.Query.ASCENDING)

            docs = query.stream()
            documents = []

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['documentId'] = doc.id
                documents.append(doc_data)

            logger.info(f"Retrieved {len(documents)} documents for session {session_id}")
            return documents

        except Exception as e:
            logger.error(f"Error getting documents: {e}", exc_info=True)
            return []


# Create singleton instance
firestore_service = FirestoreService()
