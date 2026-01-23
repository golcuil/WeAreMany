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


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _normalize_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_inbox_created_at_is_day_coarsened():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    repo = repository_module.InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="recipient", intensity="low", themes=[]),
        Candidate(candidate_id="recipient2", intensity="low", themes=[]),
        Candidate(candidate_id="recipient3", intensity="low", themes=[]),
    ]
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    client = TestClient(app)

    response = client.post(
        "/messages",
        headers=_headers("dev_sender"),
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
    )
    assert response.status_code == 200

    inbox = client.get("/inbox", headers=_headers("dev_recipient"))
    assert inbox.status_code == 200
    items = inbox.json()["items"]
    assert len(items) == 1
    created_at = _normalize_iso(items[0]["created_at"])
    assert created_at.hour == 0
    assert created_at.minute == 0
    assert created_at.second == 0
    assert created_at.microsecond == 0

    main_module.COLD_START_MIN_POOL = previous_min_pool
    app.dependency_overrides.clear()
