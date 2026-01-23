from datetime import datetime
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import main as main_module  # noqa: E402
from app.matching import Candidate  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryDedupeStore:
    def __init__(self) -> None:
        self.seen = set()

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"{sender_id}:{recipient_id}"
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


def _override_deps() -> None:
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()


def test_deliver_path_writes_inbox_and_ack():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    repo = repository_module.InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="recipient", intensity="low", themes=[]),
        Candidate(candidate_id="recipient2", intensity="low", themes=[]),
        Candidate(candidate_id="recipient3", intensity="low", themes=[]),
    ]
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    _override_deps()
    client = TestClient(app)

    response = client.post(
        "/messages",
        headers=_headers("dev_sender"),
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"

    inbox = client.get("/inbox", headers=_headers("dev_recipient"))
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    assert len(items) == 1
    created_at = items[0]["created_at"]
    assert created_at
    datetime.fromisoformat(created_at)
    inbox_item_id = items[0]["inbox_item_id"]

    ack = client.post(
        "/acknowledgements",
        headers=_headers("dev_recipient"),
        json={"inbox_item_id": inbox_item_id, "reaction": "helpful"},
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "recorded"

    ack_repeat = client.post(
        "/acknowledgements",
        headers=_headers("dev_recipient"),
        json={"inbox_item_id": inbox_item_id, "reaction": "helpful"},
    )
    assert ack_repeat.status_code == 200
    assert ack_repeat.json()["status"] == "already_recorded"

    inbox_after = client.get("/inbox", headers=_headers("dev_recipient"))
    assert inbox_after.status_code == 200
    assert inbox_after.json()["items"][0]["ack_status"] == "helpful"

    main_module.COLD_START_MIN_POOL = previous_min_pool
    app.dependency_overrides.clear()


def test_authz_blocks_cross_user_inbox_and_ack():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    repo = repository_module.InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="recipient", intensity="low", themes=[]),
        Candidate(candidate_id="recipient2", intensity="low", themes=[]),
        Candidate(candidate_id="recipient3", intensity="low", themes=[]),
    ]
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    _override_deps()
    client = TestClient(app)

    client.post(
        "/messages",
        headers=_headers("dev_sender"),
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
    )

    inbox_a = client.get("/inbox", headers=_headers("dev_recipient"))
    inbox_b = client.get("/inbox", headers=_headers("dev_other"))
    assert len(inbox_a.json()["items"]) == 1
    assert len(inbox_b.json()["items"]) == 0

    inbox_item_id = inbox_a.json()["items"][0]["inbox_item_id"]
    forbidden = client.post(
        "/acknowledgements",
        headers=_headers("dev_other"),
        json={"inbox_item_id": inbox_item_id, "reaction": "helpful"},
    )
    assert forbidden.status_code == 403

    main_module.COLD_START_MIN_POOL = previous_min_pool
    app.dependency_overrides.clear()


def test_risk_level_two_blocks_and_does_not_persist():
    repo = repository_module.InMemoryRepository()
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    _override_deps()
    client = TestClient(app)

    response = client.post(
        "/messages",
        headers=_headers("dev_sender"),
        json={"valence": "negative", "intensity": "high", "free_text": "I want to kill myself"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == 2
    assert body["crisis_action"] == "show_crisis"
    assert body["status"] == "blocked"
    assert repo.messages == {}
    assert repo.inbox_items == {}

    app.dependency_overrides.clear()
