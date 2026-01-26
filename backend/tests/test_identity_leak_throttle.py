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
from typing import Optional
from app.matching import default_matching_tuning  # noqa: E402
from app.hold_reasons import HoldReason  # noqa: E402
from app.security_event_types import SecurityEventType  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryShadowThrottle:
    def __init__(self, threshold: int = 3) -> None:
        self.threshold = threshold
        self.counts: dict[str, int] = {}

    def increment(self, principal_id: str) -> int:
        count = self.counts.get(principal_id, 0) + 1
        self.counts[principal_id] = count
        return count

    def is_throttled(self, principal_id: str) -> bool:
        return self.counts.get(principal_id, 0) >= self.threshold


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


class FakeRepo:
    def __init__(self) -> None:
        self.saved_messages = 0
        self.security_events = []

    def save_message(self, record: repository_module.MessageRecord) -> str:
        self.saved_messages += 1
        return f"msg-{self.saved_messages}"

    def save_mood(self, record: repository_module.MoodRecord) -> None:
        return None

    def record_mood_event(self, record: repository_module.MoodEventRecord) -> None:
        return None

    def upsert_eligible_principal(self, principal_id: str, intensity_bucket: str, theme_tags):
        return None

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

    def get_similar_count(
        self,
        principal_id: str,
        theme_tag: str,
        valence: str,
        window_days: int,
    ) -> int:
        return 0

    def record_security_event(self, record: repository_module.SecurityEventRecord) -> None:
        self.security_events.append(record)

    def get_matching_tuning(self):
        return default_matching_tuning()

    def update_matching_tuning(self, tuning, now):
        return None

    def get_global_matching_health(self, window_days: int = 7):
        return MatchingHealth(delivered_count=0, positive_ack_count=0, ratio=0.0)

    def get_or_create_finite_content(
        self,
        principal_id: str,
        day_key: str,
        valence_bucket: str,
        intensity_bucket: str,
        theme_id: Optional[str],
    ) -> str:
        return "content-1"


def _headers(token: str = "dev_test"):
    return {"Authorization": f"Bearer {token}"}


def _override_dependencies(repo: FakeRepo, throttle: InMemoryShadowThrottle) -> None:
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[moderation_module.get_shadow_throttle] = lambda: throttle
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()


def test_shadow_throttle_holds_on_threshold():
    client = TestClient(app)
    repo = FakeRepo()
    throttle = InMemoryShadowThrottle(threshold=3)
    _override_dependencies(repo, throttle)

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Email me at test@example.com",
    }
    first = client.post("/messages", json=payload, headers=_headers())
    second = client.post("/messages", json=payload, headers=_headers())
    count_after_second = repo.saved_messages
    third = client.post("/messages", json=payload, headers=_headers())

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert third.json()["status"] == "held"
    assert third.json()["hold_reason"] == HoldReason.IDENTITY_LEAK.value
    assert "test@example.com" not in third.json()["sanitized_text"]
    assert repo.saved_messages == count_after_second
    assert any(
        event.event_type == SecurityEventType.IDENTITY_LEAK_THROTTLE_HELD.value
        for event in repo.security_events
    )

    app.dependency_overrides.clear()


def test_non_pii_does_not_increment_or_hold():
    client = TestClient(app)
    repo = FakeRepo()
    throttle = InMemoryShadowThrottle(threshold=3)
    _override_dependencies(repo, throttle)

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Having a hard day but okay.",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is False
    assert body["hold_reason"] != HoldReason.IDENTITY_LEAK.value

    app.dependency_overrides.clear()


def test_mood_increments_shadow_throttle_on_identity_leak():
    client = TestClient(app)
    repo = FakeRepo()
    throttle = InMemoryShadowThrottle(threshold=3)
    _override_dependencies(repo, throttle)

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Reach me at test@example.com",
    }
    response = client.post("/mood", json=payload, headers=_headers())
    assert response.status_code == 200
    assert throttle.counts.get("test", 0) == 1

    app.dependency_overrides.clear()
