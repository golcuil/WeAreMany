from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import main as main_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.repository import MessageRecord, MoodEventRecord  # noqa: E402
from app.security import _verify_token  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app.hold_reasons import HoldReason  # noqa: E402


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _principal_id(token: str) -> str:
    return _verify_token(token).principal_id


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def _override_deps(repo) -> None:
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()


def _seed_moods(repo, now: datetime, principal_id: str, valence: str) -> None:
    repo.record_mood_event(
        MoodEventRecord(
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


def test_second_touch_offer_and_send_flow():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    offer_items = [item for item in items if item["item_type"] == "second_touch_offer"]
    assert len(offer_items) == 1
    offer_id = offer_items[0]["offer_id"]

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "thanks for your note"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    inbox_sender = client.get("/inbox", headers=_headers(sender_token))
    assert inbox_sender.status_code == 200
    sender_items = inbox_sender.json()["items"]
    assert any(item["item_type"] == "message" for item in sender_items)

    repeat = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "second try"},
    )
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "held"

    main_module.COLD_START_MIN_POOL = previous_min_pool
    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_on_crisis():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    repo.record_crisis_action(recipient_id, "show_crisis_screen", now=now)
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_by_monthly_cap():
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
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_by_cooldown():
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
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_by_negative_ack_disable():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    repo.block_second_touch_pair(
        sender_id,
        recipient_id,
        now + timedelta(days=30),
        permanent=False,
    )
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_by_identity_leak_disable():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    repo.block_second_touch_pair(sender_id, recipient_id, None, permanent=True)
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_after_identity_leak():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    message_id = repo.save_message(
        MessageRecord(
            principal_id=sender_id,
            valence="neutral",
            intensity="low",
            emotion=None,
            theme_tags=["calm"],
            risk_level=0,
            sanitized_text="hello",
            reid_risk=0.0,
            identity_leak=True,
        )
    )
    repo.create_inbox_item(message_id, recipient_id, "hello")
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient_token))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_send_blocked_by_monthly_cap():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    _seed_offer(repo, recipient_id, sender_id, now - timedelta(days=2))
    _seed_offer(repo, recipient_id, sender_id, now - timedelta(days=1))
    offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "hello"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "held"
    assert response.json()["hold_reason"] == HoldReason.RATE_LIMITED.value

    app.dependency_overrides.clear()


def test_second_touch_send_blocked_by_cooldown():
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
    assert response.json()["hold_reason"] == HoldReason.COOLDOWN_ACTIVE.value

    app.dependency_overrides.clear()


def test_second_touch_send_blocked_by_negative_ack_disable():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    repo.block_second_touch_pair(
        sender_id,
        recipient_id,
        now + timedelta(days=30),
        permanent=False,
    )
    offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "hello"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "held"
    assert response.json()["hold_reason"] == HoldReason.COOLDOWN_ACTIVE.value

    app.dependency_overrides.clear()


def test_second_touch_send_blocked_by_identity_leak_disable():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender_token = "dev_sender"
    recipient_token = "dev_recipient"
    sender_id = _principal_id(sender_token)
    recipient_id = _principal_id(recipient_token)
    _seed_moods(repo, now, sender_id, "positive")
    _seed_moods(repo, now, recipient_id, "positive")
    _seed_positive_pair(repo, now, sender_id, recipient_id)
    repo.block_second_touch_pair(sender_id, recipient_id, None, permanent=True)
    offer_id = repo.create_second_touch_offer(recipient_id, sender_id)
    _override_deps(repo)
    client = TestClient(app)

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient_token),
        json={"offer_id": offer_id, "free_text": "hello"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "held"
    assert response.json()["hold_reason"] == HoldReason.IDENTITY_LEAK.value

    app.dependency_overrides.clear()
