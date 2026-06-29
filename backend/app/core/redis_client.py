"""
app/core/redis_client.py
────────────────────────
Async Redis client wrapper.
Works with both local Redis (dev) and Upstash serverless Redis (prod).

Key responsibilities:
  - Recommendation caching (TTL 1hr)
  - Trending movie score cache (TTL 30min)
  - Rate limiting counters
  - Session/refresh token blacklist

Design: singleton client initialised at app startup, closed at shutdown.
"""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Called once at application startup."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    # Validate connection
    await _redis_client.ping()
    logger.info("Redis connection established")


async def close_redis() -> None:
    """Called at application shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    """FastAPI dependency — yields the redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialised — call init_redis() at startup")
    return _redis_client


# ── Helper utilities ───────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> None:
    """Serialise value to JSON and store with TTL."""
    client = get_redis()
    await client.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> Any | None:
    """Retrieve and deserialise a cached value. Returns None on miss."""
    client = get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_delete(key: str) -> None:
    client = get_redis()
    await client.delete(key)


async def cache_invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns count deleted."""
    client = get_redis()
    keys = await client.keys(pattern)
    if keys:
        return await client.delete(*keys)
    return 0


# ── Cache key builders ─────────────────────────────────────────────────────────
# Centralising key construction prevents typos and namespace collisions.

def rec_cache_key(user_id: str) -> str:
    return f"recs:user:{user_id}"

def movie_cache_key(movie_id: int) -> str:
    return f"movie:{movie_id}"

def trending_cache_key(page: int = 1) -> str:
    return f"trending:page:{page}"

def search_cache_key(query: str, filters_hash: str) -> str:
    return f"search:{query[:64]}:{filters_hash}"

def user_profile_cache_key(user_id: str) -> str:
    return f"profile:{user_id}"
