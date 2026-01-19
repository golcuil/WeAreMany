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
