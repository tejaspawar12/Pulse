"""Rate limiting utilities."""
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


class RateLimitStore(ABC):
    @abstractmethod
    def increment(self, key: str, window_seconds: int) -> int:
        """Increment counter, return current count."""
        pass

    @abstractmethod
    def is_exceeded(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if limit exceeded (does not increment)."""
        pass

    def get_count(self, key: str, window_seconds: int) -> int:
        """Return current count in window without incrementing (optional; Phase 3 AI usage)."""
        raise NotImplementedError


class InMemoryRateLimitStore(RateLimitStore):
    """For dev/single-worker deployments ONLY."""

    def __init__(self) -> None:
        self._counts: dict[str, list[datetime]] = defaultdict(list)

    def increment(self, key: str, window_seconds: int) -> int:
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        self._counts[key] = [t for t in self._counts[key] if t > cutoff]
        self._counts[key].append(now)
        return len(self._counts[key])

    def is_exceeded(self, key: str, limit: int, window_seconds: int) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        current_count = len([t for t in self._counts[key] if t > cutoff])
        return current_count > limit

    def get_count(self, key: str, window_seconds: int) -> int:
        """Return current count in window without incrementing (Phase 3 AI usage)."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        return len([t for t in self._counts[key] if t > cutoff])


_rate_limit_store: Optional[RateLimitStore] = None


def get_rate_limit_store() -> RateLimitStore:
    """Get rate limit store (singleton)."""
    global _rate_limit_store

    if _rate_limit_store is None:
        _rate_limit_store = InMemoryRateLimitStore()

    return _rate_limit_store


def check_rate_limit(key: str, limit: int, window_seconds: int) -> int:
    """
    Increment counter for key and return current count in window.
    Caller should raise HTTP 429 if return value > limit.
    """
    store = get_rate_limit_store()
    return store.increment(key, window_seconds)
