"""Firestore Service for managing user data, sessions, and messages."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from google.cloud import firestore
from src.firebase_admin_config import get_firestore_client
from src.logging_config import get_logger

# Use production-ready cache that works in Cloud Run
try:
    from src.utils.cache_production import cache
except ImportError:
    # Fallback to simple cache for backward compatibility
    from src.utils.cache import cache

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
            user_data['updated_at'] = firestore.SERVER_TIMESTAMP

            # Set or merge
            user_ref.set(user_data, merge=True)

            # Read back the document to get actual timestamp values
            # (SERVER_TIMESTAMP is a Sentinel object that can't be serialized)
            updated_doc = user_ref.get()
            result = updated_doc.to_dict() if updated_doc.exists else user_data

            logger.info(f"User profile updated: {user_id}")
            return result

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

    async def save_user_persona(self, user_id: str, persona_data: dict) -> dict:
        """
        Save user persona info for first-time users. Creates user document.
        This is a one-time operation - returns error if persona already exists.

        Args:
            user_id: Firebase UID
            persona_data: Persona data (country, ageGroup, gender, ethnicities)

        Returns:
            Created persona data with timestamps

        Raises:
            ValueError: If persona already exists for this user
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            # Check if persona already exists
            if user_doc.exists:
                existing_data = user_doc.to_dict()
                if existing_data.get('persona'):
                    logger.warning(f"Persona already exists for user {user_id}")
                    raise ValueError(f"Persona already exists for user {user_id}")

            # Add timestamp to persona data
            persona_with_timestamp = {
                **persona_data,
                'collected_at': firestore.SERVER_TIMESTAMP
            }

            # Create user document with persona
            user_data = {
                'persona': persona_with_timestamp,
                'feedback_score': 0,  # Initialize feedback score for new user
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }

            user_ref.set(user_data, merge=True)

            # Read back the document to get actual timestamp values
            created_doc = user_ref.get()
            result = created_doc.to_dict() if created_doc.exists else user_data

            logger.info(f"📋 User persona saved for first-time user: {user_id}")
            return result.get('persona', persona_data)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error saving persona for user {user_id}: {e}", exc_info=True)
            raise

    async def get_user_persona(self, user_id: str) -> Optional[dict]:
        """
        Retrieve user persona for message enrichment.
        Fast single-document read from users/{user_id}.

        Args:
            user_id: Firebase UID

        Returns:
            Persona data or None if not found
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            doc = user_ref.get()

            if doc.exists:
                user_data = doc.to_dict()
                persona = user_data.get('persona')
                if persona:
                    logger.debug(f"📋 Retrieved persona for user {user_id}")
                    return persona
            return None

        except Exception as e:
            logger.error(f"Error getting persona for user {user_id}: {e}", exc_info=True)
            return None

    async def user_has_persona(self, user_id: str) -> bool:
        """
        Check if a user has submitted persona information.
        Used during signup flow to determine if user is new or existing.

        Args:
            user_id: Firebase UID

        Returns:
            True if user has persona data, False otherwise
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            doc = user_ref.get()

            if doc.exists:
                user_data = doc.to_dict()
                has_persona = bool(user_data.get('persona'))
                logger.debug(f"User {user_id} has_persona: {has_persona}")
                return has_persona

            logger.debug(f"User {user_id} document not found")
            return False

        except Exception as e:
            logger.error(f"Error checking persona for user {user_id}: {e}", exc_info=True)
            return False

    # ==================== SESSION MANAGEMENT ====================

    async def create_session(self, user_id: str, session_id: str, title: str, mode: str = 'chat') -> dict:
        """
        Create a new chat session.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            title: Session title
            mode: Session mode - 'chat' or 'code' (default: 'chat')

        Returns:
            Created session data
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            # Use client-side timestamp to avoid read-back round trip
            now = datetime.now(timezone.utc)
            
            session_data = {
                'session_id': session_id,
                'title': title,
                'mode': mode,
                'has_documents': False,
                'vector_db_path': None,
                'created_at': now,
                'updated_at': now
            }

            session_ref.set(session_data)

            # Cache the newly created session
            cache_key = f"session:{user_id}:{session_id}"
            cache.set(cache_key, session_data, ttl_seconds=300)
            
            # Pre-cache empty messages list (new session has no messages)
            messages_cache_key = f"messages:{user_id}:{session_id}"
            cache.set(messages_cache_key, [], ttl_seconds=60)

            # Return session data immediately without read-back
            # This saves ~1 second by avoiding an extra Firestore round trip
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
        # Check cache first
        cache_key = f"session:{user_id}:{session_id}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Session {session_id} retrieved from cache")
            return cached
        
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)
            doc = session_ref.get()

            if doc.exists:
                session_data = doc.to_dict()
                # Cache for 5 minutes
                cache.set(cache_key, session_data, ttl_seconds=300)
                return session_data
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
            query = sessions_ref.order_by('updated_at', direction=firestore.Query.DESCENDING).limit(limit)

            docs = query.stream()
            sessions = [doc.to_dict() for doc in docs]

            logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions

        except Exception as e:
            logger.error(f"Error listing sessions: {e}", exc_info=True)
            return []

    async def update_session_title(self, user_id: str, session_id: str, title: str, mode: str = None, force: bool = False) -> bool:
        """
        Update session title only if current title is "New Chat" (unless force=True).
        This prevents overwriting user-modified titles.

        Args:
            user_id: Firebase UID
            session_id: Session ID
            title: New title
            mode: Optional session mode - 'chat' or 'code'
            force: If True, update title regardless of current value (for manual user edits)

        Returns:
            Success status
        """
        try:
            session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)

            # Get current session data to check existing title
            session_doc = session_ref.get()

            if not session_doc.exists:
                logger.warning(f"Session {session_id} not found for title update")
                return False

            session_data = session_doc.to_dict()
            current_title = session_data.get('title', '')

            # Build update dict
            update_dict = {
                'title': title,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add mode if provided
            if mode:
                update_dict['mode'] = mode

            # If force=True (manual user edit), always update
            if force:
                session_ref.update(update_dict)
                # Invalidate cache
                cache_key = f"session:{user_id}:{session_id}"
                cache.delete(cache_key)
                logger.info(f"✅ Session {session_id} title forcefully updated to '{title}' (manual edit)")
                return True

            # Otherwise, only update if current title is "New Chat" or "New Code Session"
            if current_title in ['New Chat', 'New Code Session']:
                session_ref.update(update_dict)
                # Invalidate cache
                cache_key = f"session:{user_id}:{session_id}"
                cache.delete(cache_key)
                logger.info(f"✅ Session {session_id} title updated from '{current_title}' to '{title}'")
                return True
            else:
                logger.info(f"⚠️ Skipping title update for session {session_id} - current title is not 'New Chat' or 'New Code Session': '{current_title}'")
                return False

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
                'updated_at': firestore.SERVER_TIMESTAMP
            })

            return True

        except Exception as e:
            logger.error(f"Error updating session timestamp: {e}", exc_info=True)
            return False

    async def find_session_by_id(self, session_id: str) -> Optional[tuple[str, dict]]:
        """
        Find a session by session_id across all users.
        This is useful when user_id is not available (e.g., unauthenticated requests).

        Args:
            session_id: Session ID to search for

        Returns:
            Tuple of (user_id, session_data) if found, None otherwise
        """
        try:
            # Query all users' sessions collections for this session_id
            users_ref = self.db.collection('users')
            users = users_ref.stream()

            for user_doc in users:
                user_id = user_doc.id
                session_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id)
                session_doc = session_ref.get()

                if session_doc.exists:
                    logger.info(f"Found session {session_id} for user {user_id}")
                    return (user_id, session_doc.to_dict())

            logger.warning(f"Session {session_id} not found in any user's sessions")
            return None

        except Exception as e:
            logger.error(f"Error finding session {session_id}: {e}", exc_info=True)
            return None

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

            # Use client-side timestamp to avoid read-back
            now = datetime.now(timezone.utc)
            
            message_data = {
                'role': role,
                'content': content,
                'audio_file_ref': audio_ref,
                'timestamp': now
            }

            # Add message
            doc_ref = messages_ref.add(message_data)
            message_id = doc_ref[1].id

            # Return immediately without read-back
            result = message_data.copy()
            result['message_id'] = message_id

            # Invalidate messages cache since we added a new message
            cache_key = f"messages:{user_id}:{session_id}"
            cache.delete(cache_key)

            # Update session timestamp (async, no await to avoid blocking)
            await self.update_session_timestamp(user_id, session_id)

            logger.info(f"Message added to session {session_id}")
            return result

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
        # Check cache first
        cache_key = f"messages:{user_id}:{session_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Messages for session {session_id} retrieved from cache (count: {len(cached)})")
            return cached
        
        try:
            messages_ref = self.db.collection('users').document(user_id).collection('sessions').document(session_id).collection('messages')
            
            # Optimize: Use limit(1) first to check if collection is empty
            # This is much faster than streaming all docs
            first_check = messages_ref.limit(1).get()
            
            if not first_check:
                # Collection is empty - cache and return immediately
                logger.info(f"Retrieved 0 messages for session {session_id} (empty collection)")
                cache.set(cache_key, [], ttl_seconds=60)
                return []
            
            # Collection has messages - fetch them all
            query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING)
            docs = query.stream()
            messages = []

            for doc in docs:
                msg_data = doc.to_dict()
                msg_data['message_id'] = doc.id
                messages.append(msg_data)

            # Cache empty lists for new sessions with short TTL
            if len(messages) == 0:
                cache.set(cache_key, messages, ttl_seconds=60)

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
                'file_ref': file_ref,
                'file_size': file_size,
                'mime_type': mime_type,
                'uploaded_at': firestore.SERVER_TIMESTAMP
            }

            # Add document
            doc_ref = documents_ref.add(document_data)
            document_id = doc_ref[1].id

            # Read back the document to get actual timestamp values
            # (SERVER_TIMESTAMP is a Sentinel object that can't be serialized)
            created_doc = doc_ref[1].get()
            result = created_doc.to_dict() if created_doc.exists else document_data
            result['document_id'] = document_id

            # Update session
            await self.update_session_timestamp(user_id, session_id)

            logger.info(f"Document added to session {session_id}")
            return result

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
            query = documents_ref.order_by('uploaded_at', direction=firestore.Query.ASCENDING)

            docs = query.stream()
            documents = []

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['document_id'] = doc.id
                documents.append(doc_data)

            logger.info(f"Retrieved {len(documents)} documents for session {session_id}")
            return documents

        except Exception as e:
            logger.error(f"Error getting documents: {e}", exc_info=True)
            return []

    # ==================== COST TRACKING ====================

    BILLING_CYCLE_DAYS = 30  # Monthly billing cycle

    async def update_user_cost(
        self,
        user_id: str,
        cost_inr: float,
        cost_usd: float,
        input_tokens: int,
        output_tokens: int
    ) -> Optional[Dict]:
        """
        Update user's cumulative cost with monthly reset logic.

        The cost tracking resets every 30 days from the billing_cycle_start date.
        If billing cycle has expired, counters are reset before adding new costs.

        Args:
            user_id: Firebase UID
            cost_inr: Cost incurred in INR for this request
            cost_usd: Cost incurred in USD for this request
            input_tokens: Input tokens used in this request
            output_tokens: Output tokens used in this request

        Returns:
            Updated cost tracking data or None on error
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            now = datetime.now(timezone.utc)

            if not user_doc.exists:
                # User document doesn't exist - create with initial cost tracking
                initial_data = {
                    'cost_tracking': {
                        'total_cost_inr': cost_inr,
                        'total_cost_usd': cost_usd,
                        'total_input_tokens': input_tokens,
                        'total_output_tokens': output_tokens,
                        'billing_cycle_start': now,
                        'last_updated': now
                    },
                    'feedback_score': 0,  # Initialize feedback score
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                user_ref.set(initial_data, merge=True)
                logger.info(f"💰 Initialized cost tracking for new user {user_id}: ₹{cost_inr:.4f}")
                return initial_data['cost_tracking']

            user_data = user_doc.to_dict()
            cost_tracking = user_data.get('cost_tracking', {})

            # Check if billing cycle needs reset
            billing_cycle_start = cost_tracking.get('billing_cycle_start')

            # Handle Firestore timestamp conversion
            if billing_cycle_start:
                if hasattr(billing_cycle_start, 'timestamp'):
                    # Firestore DatetimeWithNanoseconds
                    billing_start_dt = datetime.fromtimestamp(billing_cycle_start.timestamp(), tz=timezone.utc)
                elif isinstance(billing_cycle_start, datetime):
                    billing_start_dt = billing_cycle_start.replace(tzinfo=timezone.utc) if billing_cycle_start.tzinfo is None else billing_cycle_start
                else:
                    # Invalid format, reset
                    billing_start_dt = None
            else:
                billing_start_dt = None

            # Check if 30 days have passed
            should_reset = False
            if billing_start_dt is None:
                should_reset = True
                logger.info(f"🔄 No billing cycle found for user {user_id}, initializing new cycle")
            elif (now - billing_start_dt).days >= self.BILLING_CYCLE_DAYS:
                should_reset = True
                days_elapsed = (now - billing_start_dt).days
                logger.info(f"🔄 Billing cycle expired for user {user_id} ({days_elapsed} days), resetting counters")

            if should_reset:
                # Reset counters and start new billing cycle
                new_cost_tracking = {
                    'total_cost_inr': cost_inr,
                    'total_cost_usd': cost_usd,
                    'total_input_tokens': input_tokens,
                    'total_output_tokens': output_tokens,
                    'billing_cycle_start': now,
                    'last_updated': now
                }
            else:
                # Add to existing cumulative values
                new_cost_tracking = {
                    'total_cost_inr': cost_tracking.get('total_cost_inr', 0) + cost_inr,
                    'total_cost_usd': cost_tracking.get('total_cost_usd', 0) + cost_usd,
                    'total_input_tokens': cost_tracking.get('total_input_tokens', 0) + input_tokens,
                    'total_output_tokens': cost_tracking.get('total_output_tokens', 0) + output_tokens,
                    'billing_cycle_start': billing_start_dt,
                    'last_updated': now
                }

            # Update Firestore
            user_ref.update({
                'cost_tracking': new_cost_tracking,
                'updated_at': firestore.SERVER_TIMESTAMP
            })

            logger.info(
                f"💰 Updated cost for user {user_id}: "
                f"+₹{cost_inr:.4f} (Total: ₹{new_cost_tracking['total_cost_inr']:.4f}) | "
                f"Tokens: +{input_tokens + output_tokens} (Total: {new_cost_tracking['total_input_tokens'] + new_cost_tracking['total_output_tokens']})"
            )

            # Calculate days remaining in billing cycle for the response
            billing_start = new_cost_tracking.get('billing_cycle_start')
            if billing_start and isinstance(billing_start, datetime):
                days_elapsed = (now - billing_start).days
                new_cost_tracking['days_remaining'] = max(0, self.BILLING_CYCLE_DAYS - days_elapsed)
            else:
                new_cost_tracking['days_remaining'] = self.BILLING_CYCLE_DAYS

            return new_cost_tracking

        except Exception as e:
            logger.error(f"Error updating user cost for {user_id}: {e}", exc_info=True)
            return None

    async def update_feedback_score(self, user_id: str, is_positive: bool) -> Optional[Dict]:
        """
        Update user's feedback score (+10 for positive, -10 for negative).

        Args:
            user_id: Firebase UID
            is_positive: True for positive feedback, False for negative

        Returns:
            Updated feedback score or None
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            # Initialize user document if it doesn't exist
            if not user_doc.exists:
                initial_data = {
                    'feedback_score': 10 if is_positive else -10,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                user_ref.set(initial_data, merge=True)
                logger.info(f"✨ Initialized feedback score for new user {user_id}: {initial_data['feedback_score']}")
                return {'feedback_score': initial_data['feedback_score']}

            # Get current score and update
            user_data = user_doc.to_dict()
            current_score = user_data.get('feedback_score', 0)
            score_change = 10 if is_positive else -10
            new_score = current_score + score_change

            # Update feedback score
            user_ref.update({
                'feedback_score': new_score,
                'updated_at': firestore.SERVER_TIMESTAMP
            })

            feedback_type = "positive" if is_positive else "negative"
            logger.info(f"📊 Updated feedback for {user_id}: {feedback_type} ({score_change:+d}) -> Total: {new_score}")
            
            return {'feedback_score': new_score}

        except Exception as e:
            logger.error(f"Error updating feedback score for {user_id}: {e}", exc_info=True)
            return None

    async def get_user_cost(self, user_id: str) -> Optional[Dict]:
        """
        Get user's current cost tracking data.

        Args:
            user_id: Firebase UID

        Returns:
            Cost tracking data or None
        """
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return None

            user_data = user_doc.to_dict()
            cost_tracking = user_data.get('cost_tracking', {})

            # Calculate days remaining in billing cycle
            billing_cycle_start = cost_tracking.get('billing_cycle_start')
            days_remaining = self.BILLING_CYCLE_DAYS

            if billing_cycle_start:
                now = datetime.now(timezone.utc)
                if hasattr(billing_cycle_start, 'timestamp'):
                    billing_start_dt = datetime.fromtimestamp(billing_cycle_start.timestamp(), tz=timezone.utc)
                elif isinstance(billing_cycle_start, datetime):
                    billing_start_dt = billing_cycle_start.replace(tzinfo=timezone.utc) if billing_cycle_start.tzinfo is None else billing_cycle_start
                else:
                    billing_start_dt = now

                days_elapsed = (now - billing_start_dt).days
                days_remaining = max(0, self.BILLING_CYCLE_DAYS - days_elapsed)

            cost_tracking['days_remaining'] = days_remaining
            
            # Include feedback_score in response
            feedback_score = user_data.get('feedback_score', 0)
            cost_tracking['feedback_score'] = feedback_score
            
            return cost_tracking

        except Exception as e:
            logger.error(f"Error getting user cost for {user_id}: {e}", exc_info=True)
            return None

    async def check_user_balance(self, user_id: str) -> Dict:
        """
        Check if user has exceeded their monthly cost limit.

        Args:
            user_id: Firebase UID

        Returns:
            Dict with:
                - has_balance: bool - True if user can make requests, False if limit exceeded
                - total_cost_inr: float - Current total cost in INR
                - limit_inr: float - Monthly limit in INR
                - remaining_balance: float - Remaining balance in INR
                - message: str - Status message
        """
        from src.config import Config  # Import here to avoid circular import

        try:
            limit_inr = Config.MONTHLY_COST_LIMIT_INR

            # Get user's current cost
            cost_data = await self.get_user_cost(user_id)

            if cost_data is None:
                # New user with no cost tracking - they have full balance
                return {
                    "has_balance": True,
                    "total_cost_inr": 0.0,
                    "limit_inr": limit_inr,
                    "remaining_balance": limit_inr,
                    "message": "Balance available"
                }

            total_cost_inr = cost_data.get('total_cost_inr', 0.0)
            remaining_balance = max(0.0, limit_inr - total_cost_inr)
            has_balance = total_cost_inr < limit_inr

            if has_balance:
                message = "Balance available"
            else:
                message = f"Monthly limit exceeded! You have consumed ₹{total_cost_inr:.2f} out of ₹{limit_inr:.2f}. Please recharge to continue using the service."

            return {
                "has_balance": has_balance,
                "total_cost_inr": total_cost_inr,
                "limit_inr": limit_inr,
                "remaining_balance": remaining_balance,
                "message": message
            }

        except Exception as e:
            logger.error(f"Error checking user balance for {user_id}: {e}", exc_info=True)
            # On error, allow the request to proceed (fail open for better UX)
            return {
                "has_balance": True,
                "total_cost_inr": 0.0,
                "limit_inr": 100.0,
                "remaining_balance": 100.0,
                "message": "Balance check unavailable, proceeding"
            }


# Create singleton instance
firestore_service = FirestoreService()
