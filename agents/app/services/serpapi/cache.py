"""Disk cache for SerpAPI Google search responses (saves quota on repeat lookups)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import DATA_ROOT

CACHE_DIR = DATA_ROOT / "serpapi-cache"
SERPAPI_URL = "https://serpapi.com/search.json"


@dataclass
class SerpCacheStats:
    hits: int = 0
    apiCalls: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"hits": self.hits, "apiCalls": self.apiCalls}


# Module-level stats for the current company search (reset per run).
_active_stats: SerpCacheStats | None = None


def reset_active_stats() -> SerpCacheStats:
    global _active_stats
    _active_stats = SerpCacheStats()
    return _active_stats


def get_active_stats() -> SerpCacheStats | None:
    return _active_stats


def cache_enabled() -> bool:
    return os.getenv("SERPAPI_CACHE_DISABLED", "").lower() not in (
        "1",
        "true",
        "yes",
        "on",
    )


def cache_ttl_seconds() -> int:
    try:
        hours = float(os.getenv("SERPAPI_CACHE_TTL_HOURS", "168"))
    except ValueError:
        hours = 168.0
    return max(1, int(hours * 3600))


def _params_cache_key(params: dict[str, Any]) -> str:
    filtered = {k: v for k, v in sorted(params.items()) if k != "api_key"}
    raw = json.dumps(filtered, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_cached(key: str) -> dict[str, Any] | None:
    path = CACHE_DIR / f"{key}.json"
    if not path.is_file():
        return None
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        cached_at = float(envelope.get("cachedAt", 0))
        if time.time() - cached_at > cache_ttl_seconds():
            path.unlink(missing_ok=True)
            return None
        data = envelope.get("data")
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _write_cached(key: str, data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(
        json.dumps({"cachedAt": time.time(), "data": data}, ensure_ascii=False),
        encoding="utf-8",
    )


def cache_entry_count() -> int:
    if not CACHE_DIR.is_dir():
        return 0
    return sum(1 for p in CACHE_DIR.glob("*.json") if p.is_file())


async def serpapi_google_search(
    client: httpx.AsyncClient,
    params: dict[str, Any],
    *,
    stats: SerpCacheStats | None = None,
) -> tuple[dict[str, Any], bool]:
    """
    Google engine search via SerpAPI. Returns (response_json, from_cache).
  On non-200 HTTP, returns ({}, False) — callers handle empty organic_results.
    """
    use_stats = stats or _active_stats
    key = _params_cache_key(params)

    if cache_enabled():
        cached = _read_cached(key)
        if cached is not None:
            if use_stats:
                use_stats.hits += 1
            return cached, True

    res = await client.get(SERPAPI_URL, params=params)
    if use_stats:
        use_stats.apiCalls += 1

    if res.status_code != 200:
        return {}, False

    data = res.json()
    if cache_enabled() and isinstance(data, dict):
        _write_cached(key, data)
    return data, False
