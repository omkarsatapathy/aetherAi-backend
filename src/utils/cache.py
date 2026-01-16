"""Simple in-memory cache for frequently accessed data."""
from typing import Optional, Any
from datetime import datetime, timedelta
import threading

class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
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

# Global cache instance
cache = SimpleCache()
