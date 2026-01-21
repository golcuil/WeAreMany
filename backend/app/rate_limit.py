import time
from typing import Optional, Protocol

import redis
from fastapi import Depends, HTTPException, Request, status

from .config import (
    READ_RATE_LIMIT,
    READ_RATE_WINDOW_SECONDS,
    REDIS_URL,
    WRITE_RATE_LIMIT,
    WRITE_RATE_WINDOW_SECONDS,
)


class RateLimiter(Protocol):
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        ...


class RedisRateLimiter:
    def __init__(self, client: redis.Redis):
        self._client = client

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        count = self._client.incr(key)
        if count == 1:
            self._client.expire(key, window_seconds)
        return count <= limit


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        count, expires_at = self._data.get(key, (0, now + window_seconds))
        if now > expires_at:
            count = 0
            expires_at = now + window_seconds
        count += 1
        self._data[key] = (count, expires_at)
        return count <= limit


class FallbackRateLimiter:
    def __init__(self) -> None:
        self._in_memory = InMemoryRateLimiter()
        self._redis: Optional[RedisRateLimiter] = None

    def _ensure_redis(self) -> None:
        if self._redis is not None or not REDIS_URL:
            return
        try:
            client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            client.ping()
            self._redis = RedisRateLimiter(client)
        except redis.RedisError:
            self._redis = None

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        self._ensure_redis()
        if self._redis is None:
            return self._in_memory.allow(key, limit, window_seconds)
        try:
            return self._redis.allow(key, limit, window_seconds)
        except redis.RedisError:
            self._redis = None
            return self._in_memory.allow(key, limit, window_seconds)


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


_fallback_limiter = FallbackRateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _fallback_limiter


def _rate_key(principal_id: str, ip: str, scope: str) -> str:
    window = int(time.time() // 60)
    return f"rl:{scope}:{principal_id}:{ip}:{window}"


def rate_limit(scope: str):
    def dependency(
        request: Request,
        limiter: RateLimiter = Depends(get_rate_limiter),
    ) -> None:
        principal_id = getattr(request.state, "principal_id", "unknown")
        ip = request.client.host if request.client else "unknown"

        if scope == "write":
            limit = WRITE_RATE_LIMIT
            window = WRITE_RATE_WINDOW_SECONDS
        else:
            limit = READ_RATE_LIMIT
            window = READ_RATE_WINDOW_SECONDS

        key = _rate_key(principal_id, ip, scope)
        if not limiter.allow(key, limit, window):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    return dependency
