import re
from typing import Optional
from pathlib import Path
import sys

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryLeakThrottle:
    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0

    def check_and_increment(self, principal_id: str) -> None:
        self.count += 1
        if self.count > self.limit:
            raise HTTPException(status_code=429, detail="Too many identity leak attempts")


class PerPrincipalLeakThrottle:
    def __init__(self, limit: int):
        self.limit = limit
        self.counts = {}

    def check_and_increment(self, principal_id: str) -> None:
        count = self.counts.get(principal_id, 0) + 1
        self.counts[principal_id] = count
        if count > self.limit:
            raise HTTPException(status_code=429, detail="Too many identity leak attempts")


class FakeRepo:
    def __init__(self):
        self.saved_moods = 0
        self.saved_messages = 0
        self.crisis_actions = 0

    def save_mood(self, record: repository_module.MoodRecord) -> None:
        self.saved_moods += 1

    def save_message(self, record: repository_module.MessageRecord) -> None:
        self.saved_messages += 1

    def upsert_eligible_principal(self, principal_id: str, intensity_bucket: str, theme_tags):
        return None

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str):
        return None

    def get_eligible_candidates(self, sender_id: str, intensity_bucket: str, theme_tags, limit=50):
        return []

    def record_crisis_action(self, principal_id: str, action: str, now=None) -> None:
        self.crisis_actions += 1

    def is_in_crisis_window(self, principal_id: str, window_hours: int, now=None) -> bool:
        return False

    def get_matching_tuning(self):
        return matching_module.default_matching_tuning()

    def update_matching_tuning(self, tuning, now):
        return None

    def get_global_matching_health(self, window_days: int = 7):
        return repository_module.MatchingHealth(
            delivered_count=0,
            positive_ack_count=0,
            ratio=0.0,
        )

    def get_or_create_finite_content(
        self,
        principal_id: str,
        day_key: str,
        valence_bucket: str,
        intensity_bucket: str,
        theme_id: Optional[str],
    ) -> str:
        return "content-1"


class InMemoryRateLimiter:
    def __init__(self):
        self._data = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        count = self._data.get(key, 0) + 1
        self._data[key] = count
        return count <= limit


def _headers():
    return {"Authorization": "Bearer dev_test"}


def _headers_for(token: str):
    return {"Authorization": f"Bearer {token}"}


def _override_rate_limit():
    limiter = InMemoryRateLimiter()
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: limiter


class InMemoryDedupeStore:
    def __init__(self):
        self.seen = set()

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"{sender_id}:{recipient_id}"
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


def _override_matching():
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()


def test_identity_patterns_detected_and_removed():
    client = TestClient(app)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle(limit=10)
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Email me at test@example.com or DM me @handle, visit https://t.co/x and call +1 555 123 4567",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is True
    assert set(body["leak_types"]) >= {"email", "handle", "url", "phone", "dm_request"}
    assert "@handle" not in body["sanitized_text"]
    assert "test@example.com" not in body["sanitized_text"]
    assert "https://" not in body["sanitized_text"]
    assert not re.search(r"\+?\d[\d\s().-]{7,}\d", body["sanitized_text"])

    app.dependency_overrides.clear()


def test_social_domain_and_contact_phrase_redacted():
    client = TestClient(app)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle(limit=10)
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "Find me at instagram.com/myname and text me for details.",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity_leak"] is True
    assert set(body["leak_types"]) >= {"url", "dm_request"}
    assert "instagram.com" not in body["sanitized_text"]
    assert "text me" not in body["sanitized_text"].lower()

    app.dependency_overrides.clear()


def test_raw_text_not_logged(caplog):
    client = TestClient(app)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle(limit=10)
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "This is a secret phone 555-123-4567",
    }
    with caplog.at_level("INFO"):
        response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    logs = "\n".join(record.message for record in caplog.records)
    assert "This is a secret phone" not in logs
    assert "555-123-4567" not in logs

    app.dependency_overrides.clear()


def test_risk_level_two_skips_persistence():
    client = TestClient(app)
    fake_repo = FakeRepo()
    app.dependency_overrides[repository_module.get_repository] = lambda: fake_repo
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle(limit=10)
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "negative",
        "intensity": "high",
        "free_text": "I want to kill myself",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == 2
    assert body["status"] == "blocked"
    assert fake_repo.saved_messages == 0

    app.dependency_overrides.clear()


def test_repeated_leak_attempts_throttled():
    client = TestClient(app)
    throttle = InMemoryLeakThrottle(limit=1)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: throttle
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "DM me @handle",
    }
    assert client.post("/messages", json=payload, headers=_headers()).status_code == 200
    assert client.post("/messages", json=payload, headers=_headers()).status_code == 429

    app.dependency_overrides.clear()


@pytest.mark.parametrize("field_name", ["user_id", "principal_id", "device_id", "recipient_device_id"])
def test_rejects_principal_override_fields(field_name):
    client = TestClient(app)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle(limit=10)
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "hello",
        field_name: "override",
    }
    response = client.post("/messages", json=payload, headers=_headers())
    assert response.status_code in {400, 422}

    app.dependency_overrides.clear()


def test_leak_throttle_is_per_principal():
    client = TestClient(app)
    throttle = PerPrincipalLeakThrottle(limit=1)
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: throttle
    _override_rate_limit()
    _override_matching()

    payload = {
        "valence": "neutral",
        "intensity": "low",
        "free_text": "DM me @handle",
    }
    assert client.post("/messages", json=payload, headers=_headers_for("dev_a")).status_code == 200
    assert client.post("/messages", json=payload, headers=_headers_for("dev_a")).status_code == 429

    assert client.post("/messages", json=payload, headers=_headers_for("dev_b")).status_code == 200

    app.dependency_overrides.clear()
