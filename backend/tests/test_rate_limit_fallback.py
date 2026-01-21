from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
import redis

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _force_redis_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit_module, "REDIS_URL", "redis://localhost:1")
    monkeypatch.setattr(
        rate_limit_module.redis.Redis,
        "from_url",
        lambda *args, **kwargs: (_ for _ in ()).throw(redis.ConnectionError("down")),
    )
    monkeypatch.setattr(rate_limit_module, "_fallback_limiter", rate_limit_module.FallbackRateLimiter())


def test_rate_limit_fallback_allows_request_when_redis_down(monkeypatch: pytest.MonkeyPatch):
    _force_redis_down(monkeypatch)
    client = TestClient(app)

    response = client.get("/version", headers=_headers("dev_test"))
    assert response.status_code == 200


def test_rate_limit_fallback_enforces_limits(monkeypatch: pytest.MonkeyPatch):
    _force_redis_down(monkeypatch)
    monkeypatch.setattr(rate_limit_module, "READ_RATE_LIMIT", 2)
    monkeypatch.setattr(rate_limit_module, "READ_RATE_WINDOW_SECONDS", 60)

    client = TestClient(app)
    assert client.get("/version", headers=_headers("dev_test")).status_code == 200
    assert client.get("/version", headers=_headers("dev_test")).status_code == 200
    assert client.get("/version", headers=_headers("dev_test")).status_code == 429
