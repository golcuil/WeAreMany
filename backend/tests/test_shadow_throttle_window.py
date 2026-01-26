from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import moderation as moderation_module  # noqa: E402


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, int] = {}
        self.expire_calls = 0

    def incr(self, key: str) -> int:
        self._store[key] = self._store.get(key, 0) + 1
        return self._store[key]

    def get(self, key: str):
        value = self._store.get(key)
        if value is None:
            return None
        return str(value)

    def expire(self, key: str, _seconds: int) -> None:
        self.expire_calls += 1


def test_in_memory_shadow_throttle_fixed_window(monkeypatch):
    monkeypatch.setattr(moderation_module, "SHADOW_LEAK_WINDOW_SECONDS", 10)
    monkeypatch.setattr(moderation_module, "SHADOW_LEAK_THRESHOLD", 3)
    now = [0.0]
    throttle = moderation_module.InMemoryShadowLeakThrottle(now_fn=lambda: now[0])

    assert throttle.increment("p1") == 1
    _, expires_at = throttle._data["p1"]
    assert expires_at == 10

    now[0] = 5
    assert throttle.increment("p1") == 2
    _, expires_at_after = throttle._data["p1"]
    assert expires_at_after == 10

    now[0] = 9
    assert throttle.increment("p1") == 3
    assert throttle.is_throttled("p1") is True

    now[0] = 11
    assert throttle.increment("p1") == 1
    assert throttle.is_throttled("p1") is False


def test_redis_shadow_throttle_sets_ttl_once(monkeypatch):
    monkeypatch.setattr(moderation_module, "SHADOW_LEAK_THRESHOLD", 2)
    client = FakeRedis()
    throttle = moderation_module.RedisShadowLeakThrottle(client)

    assert throttle.increment("p2") == 1
    assert throttle.increment("p2") == 2
    assert client.expire_calls == 1
    assert throttle.is_throttled("p2") is True
