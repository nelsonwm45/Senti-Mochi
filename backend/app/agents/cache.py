
import os
import json
import hashlib
import redis
from typing import Optional, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = 60 * 60 * 24  # 24 hours - cache expires if data might have changed

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

def generate_cache_key(prefix: str, company_id: str, data_hash: str) -> str:
    """Generate a cache key for agent results."""
    return f"agent_cache:{prefix}:{company_id}:{data_hash}"

def hash_content(content: Any) -> str:
    """Generate a hash of the content for cache key generation."""
    if isinstance(content, str):
        data = content
    else:
        data = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def get_cached_result(cache_key: str) -> Optional[str]:
    """Retrieve cached result if exists."""
    try:
        client = get_redis_client()
        result = client.get(cache_key)
        if result:
            print(f"Cache HIT: {cache_key}")
            return result
        print(f"Cache MISS: {cache_key}")
        return None
    except Exception as e:
        print(f"Cache error (get): {e}")
        return None

def set_cached_result(cache_key: str, result: str, ttl: int = CACHE_TTL) -> bool:
    """Store result in cache."""
    try:
        client = get_redis_client()
        client.setex(cache_key, ttl, result)
        print(f"Cache SET: {cache_key}")
        return True
    except Exception as e:
        print(f"Cache error (set): {e}")
        return False

def invalidate_cache(company_id: str, prefix: Optional[str] = None) -> int:
    """Invalidate cache for a company. Returns number of keys deleted."""
    try:
        client = get_redis_client()
        if prefix:
            pattern = f"agent_cache:{prefix}:{company_id}:*"
        else:
            pattern = f"agent_cache:*:{company_id}:*"

        keys = list(client.scan_iter(match=pattern))
        if keys:
            deleted = client.delete(*keys)
            print(f"Cache invalidated: {deleted} keys for {company_id}")
            return deleted
        return 0
    except Exception as e:
        print(f"Cache error (invalidate): {e}")
        return 0
