import time
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402


class InMemoryLimiter:
    def __init__(self):
        self._data = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        count, expires_at = self._data.get(key, (0, now + window_seconds))
        if now > expires_at:
            count = 0
            expires_at = now + window_seconds
        count += 1
        self._data[key] = (count, expires_at)
        return count <= limit


def test_auth_required_for_version():
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200

    version = client.get("/version")
    assert version.status_code == 401


def test_rate_limit_triggers():
    client = TestClient(app)
    limiter = InMemoryLimiter()
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: limiter

    rate_limit_module.READ_RATE_LIMIT = 2
    rate_limit_module.READ_RATE_WINDOW_SECONDS = 60

    headers = {"Authorization": "Bearer dev_test"}
    assert client.get("/version", headers=headers).status_code == 200
    assert client.get("/version", headers=headers).status_code == 200
    assert client.get("/version", headers=headers).status_code == 429

    app.dependency_overrides.clear()
