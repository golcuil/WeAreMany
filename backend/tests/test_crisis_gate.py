from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.bridge import SYSTEM_SENDER_ID  # noqa: E402
from app.matching import Candidate  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_sender"):
    return {"Authorization": f"Bearer {token}"}


def _override_dependencies(repo: repository_module.InMemoryRepository) -> None:
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()


def test_sender_in_crisis_window_gets_system_message():
    client = TestClient(app)
    repo = repository_module.InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="recipient", intensity="low", themes=["calm"]),
    ]
    repo.record_crisis_action("sender", "show_resources", now=datetime.now(timezone.utc))
    _override_dependencies(repo)

    response = client.post(
        "/messages",
        headers=_headers(),
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "held"
    assert body["hold_reason"] == "crisis_window"

    sender_items = repo.list_inbox_items("sender")
    assert len(sender_items) == 1
    message = repo.messages.get(sender_items[0].message_id)
    assert message is not None
    assert message.principal_id == SYSTEM_SENDER_ID

    recipient_items = repo.list_inbox_items("recipient")
    assert recipient_items == []

    app.dependency_overrides.clear()


def test_recipient_in_crisis_window_is_excluded():
    repo = repository_module.InMemoryRepository()
    repo.upsert_eligible_principal("recipient", "low", ["calm"])
    repo.upsert_eligible_principal("other", "low", ["calm"])
    repo.record_crisis_action("recipient", "show_resources", now=datetime.now(timezone.utc))

    candidates = repo.get_eligible_candidates(
        "sender",
        "low",
        ["calm"],
        limit=10,
    )
    candidate_ids = {candidate.candidate_id for candidate in candidates}
    assert "recipient" not in candidate_ids
    assert "other" in candidate_ids


def test_crisis_window_expires():
    repo = repository_module.InMemoryRepository()
    past = datetime.now(timezone.utc) - timedelta(hours=30)
    repo.record_crisis_action("user", "show_resources", now=past)

    assert repo.is_in_crisis_window(
        "user",
        window_hours=24,
        now=datetime.now(timezone.utc),
    ) is False
