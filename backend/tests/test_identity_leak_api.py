from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.repository import MatchingHealth  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


class FakeRepo:
    def __init__(self) -> None:
        self.security_events = []

    def record_security_event(self, record: repository_module.SecurityEventRecord) -> None:
        self.security_events.append(record)

    def save_mood(self, record: repository_module.MoodRecord) -> None:
        return None

    def record_mood_event(self, record: repository_module.MoodEventRecord) -> None:
        return None

    def upsert_eligible_principal(self, principal_id: str, intensity_bucket: str, theme_tags):
        return None

    def get_similar_count(
        self,
        principal_id: str,
        theme_tag: str,
        valence: str,
        window_days: int,
    ) -> int:
        return 0

    def save_message(self, record: repository_module.MessageRecord) -> str:
        return "msg-1"

    def get_matching_health(self, principal_id: str, window_days: int = 7) -> MatchingHealth:
        return MatchingHealth(delivered_count=0, positive_ack_count=0, ratio=0.0)

    def get_affinity_map(self, sender_id: str):
        return {}

    def get_eligible_candidates(self, sender_id: str, intensity_bucket: str, theme_tags, limit=50):
        return []

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        return "inbox-1"

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str) -> None:
        return None

    def is_in_crisis_window(self, principal_id: str, window_hours: int) -> bool:
        return False


def _headers(token: str = "dev_test"):
    return {"Authorization": f"Bearer {token}"}


def _override_dependencies(repo: FakeRepo = None) -> None:
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    if repo is not None:
        app.dependency_overrides[repository_module.get_repository] = lambda: repo


def test_mood_flags_identity_leak_and_redacts():
    client = TestClient(app)
    repo = FakeRepo()
    _override_dependencies(repo)

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
    assert any(event.event_type == "identity_leak_detected" for event in repo.security_events)
    assert all(
        "test@example.com" not in str(event.meta) and "www.example.com" not in str(event.meta)
        for event in repo.security_events
    )

    app.dependency_overrides.clear()


def test_messages_flags_identity_leak_and_redacts():
    client = TestClient(app)
    repo = FakeRepo()
    _override_dependencies(repo)

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
    assert any(event.event_type == "identity_leak_detected" for event in repo.security_events)

    app.dependency_overrides.clear()


def test_messages_non_pii_keeps_identity_leak_false():
    client = TestClient(app)
    repo = FakeRepo()
    _override_dependencies(repo)

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
    assert repo.security_events == []

    app.dependency_overrides.clear()
