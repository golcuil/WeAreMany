from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.security import _verify_token  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from tools.print_second_touch_metrics import (  # noqa: E402
    SECOND_TOUCH_COUNTER_KEYS,
    format_second_touch_metrics,
)


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _principal_id(token: str) -> str:
    return _verify_token(token).principal_id


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None

    def increment(self, principal_id: str) -> None:
        return None

    def is_throttled(self, principal_id: str) -> bool:
        return False


def _override_deps(repo) -> None:
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryThrottle()
    app.dependency_overrides[moderation_module.get_shadow_throttle] = lambda: InMemoryThrottle()


def _seed_moods(repo, now: datetime, principal_id: str, valence: str) -> None:
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id=principal_id,
            created_at=now - timedelta(days=1),
            valence=valence,
            intensity="low",
            expressed_emotion=None,
            risk_level=0,
            theme_tag="calm",
        )
    )


def _seed_positive_pair(repo, now: datetime, sender_id: str, recipient_id: str) -> None:
    repo.update_second_touch_pair_positive(sender_id, recipient_id, now - timedelta(days=15))
    repo.update_second_touch_pair_positive(sender_id, recipient_id, now - timedelta(days=15))
    repo.update_second_touch_pair_positive(sender_id, recipient_id, now - timedelta(days=8))
    repo.update_second_touch_pair_positive(sender_id, recipient_id, now - timedelta(days=8))


def _seed_offer(repo, offer_to_id: str, counterpart_id: str, created_at: datetime) -> str:
    offer_id = repo.create_second_touch_offer(offer_to_id, counterpart_id)
    offer = repo.second_touch_offers[offer_id]
    offer.created_at = created_at
    return offer_id


def test_second_touch_metrics_offer_suppressed_rate_limited():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    offer_a = _seed_offer(repo, recipient_id, sender_id, now - timedelta(days=2))
    offer_b = _seed_offer(repo, recipient_id, sender_id, now - timedelta(days=1))
    repo.second_touch_offers[offer_a].used_at = now - timedelta(days=1)
    repo.second_touch_offers[offer_b].used_at = now - timedelta(days=1)
    repo.second_touch_offers[offer_a].state = "used"
    repo.second_touch_offers[offer_b].state = "used"
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200

    counters = repo.get_second_touch_counters(7)
    assert counters.get("offers_suppressed_rate_limited") == 1
    assert counters.get("offers_generated", 0) == 0

    app.dependency_overrides.clear()


def test_second_touch_metrics_send_attempted_and_queued():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "thanks"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    counters = repo.get_second_touch_counters(7)
    assert counters.get("sends_attempted") == 1
    assert counters.get("sends_queued") == 1

    app.dependency_overrides.clear()


def test_second_touch_metrics_send_held_cooldown():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    offer_id = _seed_offer(repo, recipient_id, sender_id, now - timedelta(days=40))
    repo.second_touch_offers[offer_id].used_at = now - timedelta(days=1)
    repo.second_touch_offers[offer_id].state = "used"
    new_offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": new_offer_id, "free_text": "hello"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "held"

    counters = repo.get_second_touch_counters(7)
    assert counters.get("sends_attempted") == 1
    assert counters.get("sends_held_cooldown_active") == 1

    app.dependency_overrides.clear()


def test_second_touch_metrics_identity_leak_disable():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "email me at test@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "held"

    counters = repo.get_second_touch_counters(7)
    assert counters.get("sends_attempted") == 1
    assert counters.get("sends_held_identity_leak") == 1
    assert counters.get("disables_identity_leak") == 1

    app.dependency_overrides.clear()


def test_format_second_touch_metrics_is_aggregate_only():
    counters = {"offers_generated": 2, "sends_attempted": 3}
    line = format_second_touch_metrics(counters, 7)[0]
    assert "offer_id" not in line
    assert "recipient" not in line
    assert "principal" not in line
    tokens = line.split()
    assert tokens[0] == "second_touch_window_days=7"
    for token in tokens[1:]:
        key, value = token.split("=", 1)
        assert key in {"second_touch_window_days"} | set(SECOND_TOUCH_COUNTER_KEYS) | {
            "offers_suppressed_total",
            "offers_suppressed_rate",
            "sends_held_total",
            "sends_held_rate",
        }
        assert re.fullmatch(r"-?\d+(\.\d+)?", value)
