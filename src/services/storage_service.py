"""Cloud Storage Service for managing file uploads."""
import os
import uuid
from typing import Optional, BinaryIO
from src.firebase_admin_config import get_storage_bucket
from src.logging_config import get_logger

logger = get_logger("chatbot.services.storage")


class StorageService:
    """Service for Cloud Storage operations."""

    def __init__(self):
        self.bucket = get_storage_bucket()

    def _get_user_path(self, user_id: str, file_type: str, session_id: str) -> str:
        """
        Generate path for user file in Cloud Storage.

        Args:
            user_id: Firebase UID
            file_type: Type of file (audio, documents)
            session_id: Session ID

        Returns:
            Cloud Storage path
        """
        return f"users/{user_id}/{file_type}/{session_id}"

    async def upload_audio(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        audio_data: bytes,
        content_type: str = "audio/wav"
    ) -> str:
        """
        Upload audio file to Cloud Storage.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            message_id: Message ID
            audio_data: Audio file bytes
            content_type: MIME type

        Returns:
            Cloud Storage reference (gs://...)
        """
        try:
            # Generate path
            file_path = f"{self._get_user_path(user_id, 'audio', session_id)}/{message_id}.wav"

            # Upload to Cloud Storage
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(audio_data, content_type=content_type)

            # Get reference
            file_ref = f"gs://{self.bucket.name}/{file_path}"

            logger.info(f"Audio uploaded: {file_ref}")
            return file_ref

        except Exception as e:
            logger.error(f"Error uploading audio: {e}", exc_info=True)
            raise

    async def upload_document(
        self,
        user_id: str,
        session_id: str,
        filename: str,
        file_data: bytes,
        content_type: str
    ) -> tuple[str, int]:
        """
        Upload document file to Cloud Storage.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            filename: Original filename
            file_data: File bytes
            content_type: MIME type

        Returns:
            Tuple of (Cloud Storage reference, file size)
        """
        try:
            # Generate unique filename to prevent collisions
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"

            # Generate path
            file_path = f"{self._get_user_path(user_id, 'documents', session_id)}/{unique_filename}"

            # Upload to Cloud Storage
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(file_data, content_type=content_type)

            # Set metadata
            blob.metadata = {
                'originalFilename': filename,
                'userId': user_id,
                'sessionId': session_id
            }
            blob.patch()

            # Get reference and size
            file_ref = f"gs://{self.bucket.name}/{file_path}"
            file_size = len(file_data)

            logger.info(f"Document uploaded: {file_ref} ({file_size} bytes)")
            return file_ref, file_size

        except Exception as e:
            logger.error(f"Error uploading document: {e}", exc_info=True)
            raise

    async def download_file(self, file_ref: str) -> Optional[bytes]:
        """
        Download file from Cloud Storage.

        Args:
            file_ref: Cloud Storage reference (gs://...)

        Returns:
            File bytes or None
        """
        try:
            # Parse gs:// URL
            if not file_ref.startswith('gs://'):
                raise ValueError("Invalid file reference format")

            # Extract path
            path = file_ref.replace(f"gs://{self.bucket.name}/", "")

            # Download
            blob = self.bucket.blob(path)
            data = blob.download_as_bytes()

            logger.info(f"File downloaded: {file_ref}")
            return data

        except Exception as e:
            logger.error(f"Error downloading file {file_ref}: {e}", exc_info=True)
            return None

    async def get_download_url(self, file_ref: str, expiration: int = 3600) -> Optional[str]:
        """
        Get signed URL for downloading file.

        Args:
            file_ref: Cloud Storage reference (gs://...)
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed download URL or None
        """
        try:
            # Parse gs:// URL
            if not file_ref.startswith('gs://'):
                raise ValueError("Invalid file reference format")

            # Extract path
            path = file_ref.replace(f"gs://{self.bucket.name}/", "")

            # Generate signed URL
            blob = self.bucket.blob(path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )

            logger.info(f"Generated download URL for: {file_ref}")
            return url

        except Exception as e:
            logger.error(f"Error generating download URL for {file_ref}: {e}", exc_info=True)
            return None

    async def delete_file(self, file_ref: str) -> bool:
        """
        Delete file from Cloud Storage.

        Args:
            file_ref: Cloud Storage reference (gs://...)

        Returns:
            Success status
        """
        try:
            # Parse gs:// URL
            if not file_ref.startswith('gs://'):
                raise ValueError("Invalid file reference format")

            # Extract path
            path = file_ref.replace(f"gs://{self.bucket.name}/", "")

            # Delete
            blob = self.bucket.blob(path)
            blob.delete()

            logger.info(f"File deleted: {file_ref}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file {file_ref}: {e}", exc_info=True)
            return False

    async def delete_session_files(self, user_id: str, session_id: str) -> bool:
        """
        Delete all files for a session.

        Args:
            user_id: Firebase UID
            session_id: Session ID

        Returns:
            Success status
        """
        try:
            # Delete audio files
            audio_prefix = f"{self._get_user_path(user_id, 'audio', session_id)}/"
            audio_blobs = self.bucket.list_blobs(prefix=audio_prefix)

            for blob in audio_blobs:
                blob.delete()

            # Delete document files
            docs_prefix = f"{self._get_user_path(user_id, 'documents', session_id)}/"
            doc_blobs = self.bucket.list_blobs(prefix=docs_prefix)

            for blob in doc_blobs:
                blob.delete()

            logger.info(f"All files deleted for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session files: {e}", exc_info=True)
            return False

    async def list_user_files(self, user_id: str, file_type: Optional[str] = None) -> list:
        """
        List all files for a user.

        Args:
            user_id: Firebase UID
            file_type: Optional filter by type (audio, documents)

        Returns:
            List of file references
        """
        try:
            if file_type:
                prefix = f"users/{user_id}/{file_type}/"
            else:
                prefix = f"users/{user_id}/"

            blobs = self.bucket.list_blobs(prefix=prefix)
            file_refs = [f"gs://{self.bucket.name}/{blob.name}" for blob in blobs]

            logger.info(f"Listed {len(file_refs)} files for user {user_id}")
            return file_refs

        except Exception as e:
            logger.error(f"Error listing user files: {e}", exc_info=True)
            return []


# Create singleton instance
storage_service = StorageService()
