"""
Caching Layer - Lightweight in-memory cache for responses.

Phase 7: Provides a cache with TTL, simple eviction, and regeneration hooks.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional
import threading
import time
import logging

from Back_End.response_engine.types import Response


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    value: Any
    cached_at: datetime
    expires_at: Optional[datetime]

    def is_valid(self) -> bool:
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at


class ResponseCache:
    """Simple in-memory cache for Response objects."""

    def __init__(self, default_ttl_seconds: int = 3600, max_entries: int = 500):
        self.default_ttl_seconds = default_ttl_seconds
        self.max_entries = max_entries
        self._lock = threading.RLock()
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Response]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if not entry.is_valid():
                self._cache.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Response, ttl_seconds: Optional[int] = None) -> None:
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
            self._cache[key] = CacheEntry(value=value, cached_at=datetime.utcnow(), expires_at=expires_at)
            self._evict_if_needed()

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def get_or_generate(
        self,
        key: str,
        generator: Callable[[], Response],
        ttl_seconds: Optional[int] = None,
    ) -> Response:
        cached = self.get(key)
        if cached:
            return cached
        response = generator()
        self.set(key, response, ttl_seconds=ttl_seconds)
        return response

    def _evict_if_needed(self) -> None:
        if len(self._cache) <= self.max_entries:
            return
        # Evict oldest entries based on cached_at
        sorted_items = sorted(self._cache.items(), key=lambda kv: kv[1].cached_at)
        to_remove = len(self._cache) - self.max_entries
        for i in range(to_remove):
            key, _ = sorted_items[i]
            self._cache.pop(key, None)


class ResponseCacheManager:
    """High-level cache manager to integrate with Response metadata."""

    def __init__(self, cache: Optional[ResponseCache] = None):
        self.cache = cache or ResponseCache()

    def cache_response(self, response: Response, ttl_seconds: Optional[int] = None) -> None:
        key = response.response_id
        self.cache.set(key, response, ttl_seconds=ttl_seconds)
        response.cached_at = datetime.utcnow()
        if ttl_seconds:
            response.expires_at = response.cached_at + timedelta(seconds=ttl_seconds)

    def get_cached_response(self, response_id: str) -> Optional[Response]:
        return self.cache.get(response_id)

    def invalidate_response(self, response_id: str) -> None:
        self.cache.invalidate(response_id)

    def cache_or_regenerate(
        self,
        response_id: str,
        generator: Callable[[], Response],
        ttl_seconds: Optional[int] = None,
    ) -> Response:
        start = time.time()
        response = self.cache.get_or_generate(response_id, generator, ttl_seconds=ttl_seconds)
        duration_ms = (time.time() - start) * 1000
        logger.info("Cache lookup for %s took %.2fms", response_id, duration_ms)
        return response

