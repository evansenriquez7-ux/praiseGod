import os
import json
from typing import Any, Optional

try:
    import redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    # If we are in testing or local dev without redis, this might fail on connect,
    # so we can use a try-except block around connection.
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False
    _fallback_cache = {}

def get_cache(key: str) -> Optional[Any]:
    if REDIS_AVAILABLE:
        val = r.get(key)
        if val:
            return json.loads(val)
        return None
    else:
        return _fallback_cache.get(key)

def set_cache(key: str, value: Any, ex: int = 3600) -> None:
    if REDIS_AVAILABLE:
        r.set(key, json.dumps(value), ex=ex)
    else:
        _fallback_cache[key] = value

def delete_cache(key: str) -> None:
    if REDIS_AVAILABLE:
        r.delete(key)
    else:
        if key in _fallback_cache:
            del _fallback_cache[key]
