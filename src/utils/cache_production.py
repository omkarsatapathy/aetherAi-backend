"""Production-ready cache with Redis support for Cloud Run deployment."""
from typing import Optional, Any
from datetime import datetime, timedelta
import threading
import os
import json
import logging

logger = logging.getLogger("chatbot.cache")


class SimpleCache:
    """Thread-safe in-memory cache with TTL support (for local development)."""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
        logger.info("🔧 Using in-memory cache (local development mode)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.utcnow() < expiry:
                    return value
                else:
                    # Expired - remove it
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL (default 5 minutes)."""
        with self._lock:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern (simple startswith)."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]


class RedisCache:
    """Redis-backed cache for production (Cloud Run with Memorystore)."""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis cache."""
        try:
            import redis
            from redis.exceptions import RedisError
            
            self.redis_url = redis_url or os.getenv('REDIS_URL')
            if not self.redis_url:
                raise ValueError("REDIS_URL not configured")
            
            # Parse Redis URL
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"🚀 Connected to Redis cache: {self._mask_url(self.redis_url)}")
            
        except ImportError:
            logger.error("❌ Redis library not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def _mask_url(self, url: str) -> str:
        """Mask password in URL for logging."""
        if ':' in url and '@' in url:
            parts = url.split('@')
            return f"{parts[0].split(':')[0]}://***@{parts[1]}"
        return url
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        # Convert datetime objects to ISO format
        if isinstance(value, datetime):
            return json.dumps({'__datetime__': value.isoformat()})
        
        # Handle dictionaries with datetime values
        if isinstance(value, dict):
            serialized = {}
            for k, v in value.items():
                if isinstance(v, datetime):
                    serialized[k] = {'__datetime__': v.isoformat()}
                else:
                    serialized[k] = v
            return json.dumps(serialized)
        
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        
        return json.dumps(value)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize value from Redis storage."""
        if value is None:
            return None
        
        data = json.loads(value)
        
        # Handle datetime objects
        if isinstance(data, dict) and '__datetime__' in data:
            from datetime import datetime
            return datetime.fromisoformat(data['__datetime__'])
        
        # Handle dictionaries with datetime values
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if isinstance(v, dict) and '__datetime__' in v:
                    from datetime import datetime
                    result[k] = datetime.fromisoformat(v['__datetime__'])
                else:
                    result[k] = v
            return result
        
        return data
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            value = self.client.get(key)
            if value:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in Redis cache with TTL."""
        try:
            serialized = self._serialize(value)
            self.client.setex(key, ttl_seconds, serialized)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
    
    def delete(self, key: str):
        """Delete value from Redis cache."""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
    
    def clear(self):
        """Clear all cache (use with caution in production!)."""
        try:
            self.client.flushdb()
            logger.warning("⚠️ Cache cleared (flushdb)")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        try:
            # Use SCAN to avoid blocking
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=f"{pattern}*", count=100)
                if keys:
                    self.client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Cache delete_pattern error for {pattern}: {e}")


class FirestoreCache:
    """Firestore-based cache (free alternative for Cloud Run)."""
    
    def __init__(self):
        """Initialize Firestore cache."""
        from src.firebase_admin_config import get_firestore_client
        self.db = get_firestore_client()
        self.cache_collection = self.db.collection('_cache')
        logger.info("💾 Using Firestore-based cache (free tier)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Firestore cache."""
        try:
            doc = self.cache_collection.document(key).get()
            if doc.exists:
                data = doc.to_dict()
                # Check expiry
                if data.get('expires_at') and datetime.utcnow() < data['expires_at'].replace(tzinfo=None):
                    return data.get('value')
                else:
                    # Expired - delete it
                    self.delete(key)
            return None
        except Exception as e:
            logger.warning(f"Firestore cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in Firestore cache with TTL."""
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self.cache_collection.document(key).set({
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Firestore cache set error for {key}: {e}")
    
    def delete(self, key: str):
        """Delete value from Firestore cache."""
        try:
            self.cache_collection.document(key).delete()
        except Exception as e:
            logger.warning(f"Firestore cache delete error for {key}: {e}")
    
    def clear(self):
        """Clear all cache."""
        try:
            docs = self.cache_collection.list_documents()
            for doc in docs:
                doc.delete()
        except Exception as e:
            logger.error(f"Firestore cache clear error: {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        # Firestore doesn't support pattern matching efficiently
        # Would need to query and filter - skipping for now
        logger.warning("delete_pattern not efficiently supported in Firestore cache")


def create_cache():
    """
    Factory function to create appropriate cache based on environment.
    
    Priority:
    1. Redis (if REDIS_URL is set) - Best for production
    2. Firestore cache (if USE_FIRESTORE_CACHE=true) - Free alternative
    3. In-memory cache - Local development
    """
    # Check for Redis
    if os.getenv('REDIS_URL'):
        try:
            return RedisCache()
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            logger.warning("Falling back to in-memory cache")
    
    # Check for Firestore cache
    if os.getenv('USE_FIRESTORE_CACHE', '').lower() == 'true':
        try:
            return FirestoreCache()
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore cache: {e}")
            logger.warning("Falling back to in-memory cache")
    
    # Default: in-memory cache
    return SimpleCache()


# Global cache instance
cache = create_cache()
