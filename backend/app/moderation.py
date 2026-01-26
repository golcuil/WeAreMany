import re
import time
from dataclasses import dataclass
from typing import List, Optional, Protocol

import redis
from fastapi import HTTPException, status

from .config import (
    LEAK_ATTEMPT_LIMIT,
    LEAK_ATTEMPT_WINDOW_SECONDS,
    REDIS_URL,
    SHADOW_LEAK_THRESHOLD,
    SHADOW_LEAK_WINDOW_SECONDS,
)

PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|gg|me|co)(?:/\S+)?\b",
    re.IGNORECASE,
)
SOCIAL_RE = re.compile(
    r"\b(?:instagram|insta|tiktok|snapchat|telegram|whatsapp|twitter|x|facebook|fb|discord|linkedin)"
    r"\.(?:com|me|gg)(?:/\S+)?\b",
    re.IGNORECASE,
)
HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{2,}")
DM_RE = re.compile(r"\b(dm me|message me|reach me|contact me|add me|text me|call me)\b", re.IGNORECASE)
SELF_HARM_RE = re.compile(r"\b(suicide|kill myself|end it|self harm)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ModerationResult:
    sanitized_text: Optional[str]
    risk_level: int
    reid_risk: float
    identity_leak: bool
    leak_types: List[str]


class LeakThrottle(Protocol):
    def check_and_increment(self, principal_id: str) -> None:
        ...


class ShadowLeakThrottle(Protocol):
    def increment(self, principal_id: str) -> int:
        ...

    def is_throttled(self, principal_id: str) -> bool:
        ...


class RedisLeakThrottle:
    def __init__(self, client: redis.Redis):
        self._client = client

    def check_and_increment(self, principal_id: str) -> None:
        key = _leak_key(principal_id)
        count = self._client.incr(key)
        if count == 1:
            self._client.expire(key, LEAK_ATTEMPT_WINDOW_SECONDS)
        if count > LEAK_ATTEMPT_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many identity leak attempts",
            )


def _leak_key(principal_id: str) -> str:
    window = int(time.time() // LEAK_ATTEMPT_WINDOW_SECONDS)
    return f"leak:{principal_id}:{window}"


def get_leak_throttle() -> LeakThrottle:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return RedisLeakThrottle(client)


class RedisShadowLeakThrottle:
    def __init__(self, client: redis.Redis):
        self._client = client

    def increment(self, principal_id: str) -> int:
        key = _shadow_key(principal_id)
        count = int(self._client.incr(key))
        if count == 1:
            self._client.expire(key, SHADOW_LEAK_WINDOW_SECONDS)
        return count

    def is_throttled(self, principal_id: str) -> bool:
        value = self._client.get(_shadow_key(principal_id))
        if value is None:
            return False
        return int(value) >= SHADOW_LEAK_THRESHOLD


class InMemoryShadowLeakThrottle:
    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float]] = {}

    def increment(self, principal_id: str) -> int:
        now = time.time()
        count, expires_at = self._data.get(principal_id, (0, now + SHADOW_LEAK_WINDOW_SECONDS))
        if now > expires_at:
            count = 0
            expires_at = now + SHADOW_LEAK_WINDOW_SECONDS
        count += 1
        self._data[principal_id] = (count, expires_at)
        return count

    def is_throttled(self, principal_id: str) -> bool:
        now = time.time()
        count, expires_at = self._data.get(principal_id, (0, now + SHADOW_LEAK_WINDOW_SECONDS))
        if now > expires_at:
            return False
        return count >= SHADOW_LEAK_THRESHOLD


class FallbackShadowLeakThrottle:
    def __init__(self) -> None:
        self._in_memory = InMemoryShadowLeakThrottle()
        self._redis: Optional[RedisShadowLeakThrottle] = None

    def _ensure_redis(self) -> None:
        if self._redis is not None or not REDIS_URL:
            return
        try:
            client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            client.ping()
            self._redis = RedisShadowLeakThrottle(client)
        except redis.RedisError:
            self._redis = None

    def increment(self, principal_id: str) -> int:
        self._ensure_redis()
        if self._redis is None:
            return self._in_memory.increment(principal_id)
        try:
            return self._redis.increment(principal_id)
        except redis.RedisError:
            self._redis = None
            return self._in_memory.increment(principal_id)

    def is_throttled(self, principal_id: str) -> bool:
        self._ensure_redis()
        if self._redis is None:
            return self._in_memory.is_throttled(principal_id)
        try:
            return self._redis.is_throttled(principal_id)
        except redis.RedisError:
            self._redis = None
            return self._in_memory.is_throttled(principal_id)


def _shadow_key(principal_id: str) -> str:
    return f"shadow_leak:{principal_id}"


_shadow_throttle = FallbackShadowLeakThrottle()


def get_shadow_throttle() -> ShadowLeakThrottle:
    return _shadow_throttle


def detect_identity_leaks(text: str) -> List[str]:
    leak_types: List[str] = []
    if PHONE_RE.search(text):
        leak_types.append("phone")
    if EMAIL_RE.search(text):
        leak_types.append("email")
    if URL_RE.search(text):
        leak_types.append("url")
    if DOMAIN_RE.search(text):
        leak_types.append("url")
    if SOCIAL_RE.search(text):
        leak_types.append("url")
    if HANDLE_RE.search(text):
        leak_types.append("handle")
    if DM_RE.search(text):
        leak_types.append("dm_request")
    return leak_types


def strip_identity(text: str) -> str:
    text = PHONE_RE.sub("[redacted]", text)
    text = EMAIL_RE.sub("[redacted]", text)
    text = URL_RE.sub("[redacted]", text)
    text = DOMAIN_RE.sub("[redacted]", text)
    text = SOCIAL_RE.sub("[redacted]", text)
    text = HANDLE_RE.sub("[redacted]", text)
    text = DM_RE.sub("[redacted]", text)
    return text


def rewrite_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "I want to share something difficult."
    return stripped


def score_reid_risk(leak_types: List[str]) -> float:
    return min(1.0, 0.2 * len(leak_types))


def classify_risk(text: str) -> int:
    if SELF_HARM_RE.search(text):
        return 2
    return 0


def moderate_text(text: str, principal_id: str, throttle: LeakThrottle) -> ModerationResult:
    leak_types = detect_identity_leaks(text)
    if leak_types:
        throttle.check_and_increment(principal_id)

    risk_level = classify_risk(text)
    sanitized = rewrite_text(strip_identity(text)) if text else None
    reid_risk = score_reid_risk(leak_types)

    return ModerationResult(
        sanitized_text=sanitized,
        risk_level=risk_level,
        reid_risk=reid_risk,
        identity_leak=bool(leak_types),
        leak_types=leak_types,
    )
