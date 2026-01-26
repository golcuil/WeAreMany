import json
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.events import EventName, MoodSubmittedEvent, validate_event  # noqa: E402
from app.main import app  # noqa: E402
from app import events as events_module  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from typing import Optional


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0

    def check_and_increment(self, principal_id: str) -> None:
        self.count += 1
        if self.count > self.limit:
            raise Exception("throttled")


class InMemoryDedupeStore:
    def __init__(self):
        self.seen = set()

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"{sender_id}:{recipient_id}"
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


def _headers():
    return {"Authorization": "Bearer dev_test"}


def _override_rate_limit():
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()


class FakeRepo:
    def save_mood(self, record: repository_module.MoodRecord) -> None:
        return None

    def record_mood_event(self, record: repository_module.MoodEventRecord) -> None:
        return None

    def save_message(self, record: repository_module.MessageRecord) -> str:
        return "msg-1"

    def upsert_eligible_principal(self, principal_id: str, intensity_bucket: str, theme_tags):
        return None

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str):
        return None

    def get_eligible_candidates(self, sender_id: str, intensity_bucket: str, theme_tags, limit=50):
        return []

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        return "inbox-1"

    def acknowledge(self, inbox_item_id: str, recipient_id: str, reaction: str) -> str:
        return "recorded"

    def get_helped_count(self, principal_id: str) -> int:
        return 0

    def record_affinity(self, sender_id: str, theme_id: str, delta: float) -> None:
        return None

    def get_affinity_map(self, sender_id: str):
        return {}

    def record_crisis_action(self, principal_id: str, action: str, now=None) -> None:
        return None

    def is_in_crisis_window(self, principal_id: str, window_hours: int, now=None) -> bool:
        return False

    def get_matching_health(self, principal_id: str, window_days: int = 7):
        return repository_module.MatchingHealth(
            delivered_count=0,
            positive_ack_count=0,
            ratio=0.0,
        )

    def record_security_event(self, record: repository_module.SecurityEventRecord) -> None:
        return None

    def prune_security_events(self, now, retention_days=None) -> int:
        return 0

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

    def get_similar_count(self, principal_id: str, theme_tag: str, valence: str, window_days: int) -> int:
        return 0


def test_event_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        MoodSubmittedEvent(
            request_id="req",
            intensity_bucket="low",
            risk_bucket=0,
            has_free_text=True,
            unknown_field="nope",
        )


def test_events_emit_without_forbidden_keys():
    client = TestClient(app)
    store = events_module.InMemoryEventStore()
    app.dependency_overrides[events_module.get_event_emitter] = lambda: store
    app.dependency_overrides[repository_module.get_repository] = lambda: FakeRepo()
    app.dependency_overrides[moderation_module.get_leak_throttle] = (
        lambda: InMemoryLeakThrottle(limit=10)
    )
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    _override_rate_limit()

    client.post(
        "/mood",
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
        headers=_headers(),
    )
    client.post(
        "/messages",
        json={"valence": "neutral", "intensity": "low", "free_text": "DM me @handle"},
        headers=_headers(),
    )
    client.post(
        "/match/simulate",
        json={
            "risk_level": 0,
            "intensity": "low",
            "themes": [],
            "candidates": [
                {"candidate_id": "c1", "intensity": "low", "themes": []},
                {"candidate_id": "c2", "intensity": "low", "themes": []},
                {"candidate_id": "c3", "intensity": "low", "themes": []},
            ],
        },
        headers=_headers(),
    )

    forbidden_keys = {
        "free_text",
        "sanitized_text",
        "phone",
        "email",
        "url",
        "authorization",
        "principal_id",
        "recipient_id",
        "message_id",
        "device_id",
    }

    for record in store.records:
        payload = record.payload.model_dump()
        serialized = json.dumps(payload)
        for key in forbidden_keys:
            assert key not in payload
        assert "test@example.com" not in serialized
        assert "@handle" not in serialized

    app.dependency_overrides.clear()


def test_validate_event_accepts_known_payloads():
    payload = {
        "request_id": "req",
        "intensity_bucket": "low",
        "risk_bucket": 0,
        "has_free_text": False,
    }
    validated = validate_event(EventName.MOOD_SUBMITTED, payload)
    assert validated.request_id == "req"
