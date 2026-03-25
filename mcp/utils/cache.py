"""
Simple in-memory TTL cache for integration API responses.

Avoids redundant external API calls within short time windows.
"""

import time
from typing import Any, Optional, Callable
from functools import wraps
import structlog

logger = structlog.get_logger()

_cache: dict[str, tuple[float, Any]] = {}


def get_cached(key: str, ttl_seconds: float = 30.0) -> Optional[Any]:
    """Return cached value if still within TTL, else None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > ttl_seconds:
        del _cache[key]
        return None
    return value


def set_cached(key: str, value: Any) -> None:
    """Store value in cache with current timestamp."""
    _cache[key] = (time.monotonic(), value)


def invalidate(prefix: str = "") -> int:
    """Invalidate cache entries matching prefix. Returns count removed."""
    if not prefix:
        count = len(_cache)
        _cache.clear()
        return count
    keys = [k for k in _cache if k.startswith(prefix)]
    for k in keys:
        del _cache[k]
    return len(keys)


def cached(ttl_seconds: float = 30.0, key_prefix: str = ""):
    """Decorator: cache function return value for ttl_seconds."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix or fn.__qualname__}:{args}:{sorted(kwargs.items())}"
            hit = get_cached(cache_key, ttl_seconds)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            set_cached(cache_key, result)
            return result

        return wrapper

    return decorator
