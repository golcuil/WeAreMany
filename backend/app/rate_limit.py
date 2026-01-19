import time
from typing import Protocol

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


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_rate_limiter() -> RateLimiter:
    return RedisRateLimiter(get_redis_client())


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
