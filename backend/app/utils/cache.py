"""In-memory TTL cache for API responses and computed results."""
import time
import threading
import hashlib
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_store: dict[str, tuple[float, Any]] = {}  # key -> (expires_at, value)
_hits = 0
_misses = 0


def _make_key(*parts: Any) -> str:
    """Build a deterministic cache key from arbitrary parts."""
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def cache_get(key: str) -> Optional[Any]:
    """Return cached value if it exists and hasn't expired, else None."""
    global _hits, _misses
    with _lock:
        entry = _store.get(key)
        if entry is None:
            _misses += 1
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del _store[key]
            _misses += 1
            return None
        _hits += 1
        return value


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Store a value with a TTL (default 5 minutes)."""
    with _lock:
        _store[key] = (time.time() + ttl_seconds, value)


def cache_delete(key: str) -> None:
    """Delete a specific key."""
    with _lock:
        _store.pop(key, None)


def cache_invalidate_prefix(prefix: str) -> int:
    """Delete all keys that start with the given prefix. Returns count deleted."""
    with _lock:
        to_delete = [k for k in _store if k.startswith(prefix)]
        for k in to_delete:
            del _store[k]
        if to_delete:
            logger.debug("Cache invalidated %d keys with prefix %s", len(to_delete), prefix)
        return len(to_delete)


def cache_clear() -> int:
    """Clear the entire cache. Returns count deleted."""
    with _lock:
        count = len(_store)
        _store.clear()
        return count


def cache_stats() -> dict:
    """Return cache statistics."""
    with _lock:
        now = time.time()
        active = sum(1 for _, (exp, _) in _store.items() if exp > now)
        return {
            "total_keys": len(_store),
            "active_keys": active,
            "expired_keys": len(_store) - active,
            "hits": _hits,
            "misses": _misses,
            "hit_rate": round(_hits / max(_hits + _misses, 1) * 100, 1),
        }


# ── Prefixes for organized invalidation ──────────────────────────
# These are used as key prefixes so we can selectively invalidate groups.
PREFIX_ACCOUNTS = "accounts:"
PREFIX_AUDIENCES = "audiences:"
PREFIX_RECOMMENDATIONS = "recs:"
PREFIX_BENCHMARKS = "benchmarks:"
PREFIX_METRICS = "metrics:"
PREFIX_SETTINGS = "settings:"


# ── TTL constants (seconds) ──────────────────────────────────────
TTL_ACCOUNTS = 300       # 5 min
TTL_AUDIENCES = 300      # 5 min
TTL_RECOMMENDATIONS = 600  # 10 min
TTL_BENCHMARKS = 1800    # 30 min
TTL_METRICS = 900        # 15 min
TTL_SETTINGS = 3600      # 1 hour


def cached(prefix: str, ttl: int = 300):
    """
    Decorator for caching function results.

    The cache key is built from the prefix + all function arguments.
    Works on regular functions (not async).

    Usage:
        @cached(PREFIX_ACCOUNTS, TTL_ACCOUNTS)
        def list_accounts(db):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Build key from prefix + function name + args (skip db sessions)
            key_parts = [prefix, func.__name__]
            for a in args:
                if hasattr(a, "bind"):  # skip SQLAlchemy sessions
                    continue
                key_parts.append(a)
            for k, v in sorted(kwargs.items()):
                if hasattr(v, "bind"):
                    continue
                key_parts.append(f"{k}={v}")
            key = prefix + _make_key(*key_parts)

            result = cache_get(key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            if result is not None:
                cache_set(key, result, ttl)
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
