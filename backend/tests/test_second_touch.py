from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import main as main_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.repository import MessageRecord, MoodEventRecord  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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


def test_second_touch_offer_and_send_flow():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender = "dev_sender"
    recipient = "dev_recipient"
    _seed_moods(repo, now, sender, "positive")
    _seed_moods(repo, now, recipient, "positive")
    _seed_positive_pair(repo, now, sender, recipient)
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient))
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    offer_items = [item for item in items if item["item_type"] == "second_touch_offer"]
    assert len(offer_items) == 1
    offer_id = offer_items[0]["offer_id"]

    response = client.post(
        "/second_touch/send",
        headers=_headers(recipient),
        json={"offer_id": offer_id, "free_text": "thanks for your note"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    inbox_sender = client.get("/inbox", headers=_headers(sender))
    assert inbox_sender.status_code == 200
    sender_items = inbox_sender.json()["items"]
    assert any(item["item_type"] == "message" for item in sender_items)

    repeat = client.post(
        "/second_touch/send",
        headers=_headers(recipient),
        json={"offer_id": offer_id, "free_text": "second try"},
    )
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "held"

    main_module.COLD_START_MIN_POOL = previous_min_pool
    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_on_crisis():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender = "dev_sender"
    recipient = "dev_recipient"
    _seed_moods(repo, now, sender, "positive")
    _seed_moods(repo, now, recipient, "positive")
    _seed_positive_pair(repo, now, sender, recipient)
    repo.record_crisis_action(recipient, "show_crisis", now=now)
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()


def test_second_touch_offer_blocked_after_identity_leak():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    sender = "dev_sender"
    recipient = "dev_recipient"
    _seed_moods(repo, now, sender, "positive")
    _seed_moods(repo, now, recipient, "positive")
    _seed_positive_pair(repo, now, sender, recipient)
    message_id = repo.save_message(
        MessageRecord(
            principal_id=sender,
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
    repo.create_inbox_item(message_id, recipient, "hello")
    _override_deps(repo)
    client = TestClient(app)

    inbox = client.get("/inbox", headers=_headers(recipient))
    assert inbox.status_code == 200
    assert not any(item["item_type"] == "second_touch_offer" for item in inbox.json()["items"])

    app.dependency_overrides.clear()
