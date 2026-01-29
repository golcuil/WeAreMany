from datetime import datetime, timedelta, timezone
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


def _offset_minutes_to_noon(now: datetime) -> int:
    desired_offset_hours = 12 - now.hour
    if desired_offset_hours > 12:
        desired_offset_hours -= 24
    if desired_offset_hours < -12:
        desired_offset_hours += 24
    return int(desired_offset_hours * 60)


def _normalize_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_inbox_created_at_is_day_coarsened():
    previous_min_pool = main_module.COLD_START_MIN_POOL
    main_module.COLD_START_MIN_POOL = 1
    previous_match_min_pool = matching_module.MATCH_MIN_POOL_K
    matching_module.MATCH_MIN_POOL_K = 1
    repo = repository_module.InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="recipient", intensity="low", themes=[]),
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

    now = datetime.now(timezone.utc)
    repo.set_last_known_timezone_offset("recipient", _offset_minutes_to_noon(now))
    repo.deliver_pending_messages(now + timedelta(minutes=20), batch_size=1, default_tz_offset_minutes=0)

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
    matching_module.MATCH_MIN_POOL_K = previous_match_min_pool
    app.dependency_overrides.clear()
