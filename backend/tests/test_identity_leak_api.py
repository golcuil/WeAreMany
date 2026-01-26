from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_test"):
    return {"Authorization": f"Bearer {token}"}


def _override_dependencies() -> None:
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()


def test_mood_flags_identity_leak_and_redacts():
    client = TestClient(app)
    _override_dependencies()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Email me at test@example.com or visit www.example.com",
    }
    response = client.post("/mood", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is True
    assert "test@example.com" not in body["sanitized_text"]
    assert "www.example.com" not in body["sanitized_text"]

    app.dependency_overrides.clear()


def test_messages_flags_identity_leak_and_redacts():
    client = TestClient(app)
    _override_dependencies()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Call me at +1 (555) 123-4567",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is True
    assert "+1" not in body["sanitized_text"]
    assert "123-4567" not in body["sanitized_text"]

    app.dependency_overrides.clear()


def test_messages_non_pii_keeps_identity_leak_false():
    client = TestClient(app)
    _override_dependencies()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "I am having a hard day and could use support.",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is False
    assert "hard day" in body["sanitized_text"]

    app.dependency_overrides.clear()
