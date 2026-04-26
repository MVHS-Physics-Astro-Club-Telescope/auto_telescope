"""Disk-backed cache for condition API responses.

Why disk-backed (not in-memory): the Pi may reboot mid-night; we'd rather replay
the last good forecast than fail open during a brief outage. ``diskcache`` is
SQLite-backed, persistent, and process-safe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import diskcache


class ConditionsCache:
    """Thin wrapper around diskcache.Cache with TTL semantics."""

    def __init__(self, cache_dir: Path, default_ttl_seconds: int = 900) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(cache_dir))
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Any | None:
        """Return cached value or None if absent / expired."""
        return self._cache.get(key, default=None)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Cache a value with TTL (default from constructor)."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._cache.set(key, value, expire=ttl)

    def clear(self) -> None:
        """Drop all cached entries (mostly for tests)."""
        self._cache.clear()

    def close(self) -> None:
        """Release the underlying SQLite handle."""
        self._cache.close()

    def __enter__(self) -> ConditionsCache:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
