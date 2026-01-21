from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import events as events_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class FakeRepo:
    def __init__(self) -> None:
        self.saved_moods = 0
        self.upserts = 0
        self.mood_events = 0

    def save_mood(self, record: repository_module.MoodRecord) -> None:
        self.saved_moods += 1

    def upsert_eligible_principal(
        self,
        principal_id: str,
        intensity_bucket: str,
        theme_tags: list[str],
    ) -> None:
        self.upserts += 1

    def record_mood_event(self, record: repository_module.MoodEventRecord) -> None:
        self.mood_events += 1


class FakeEmitter:
    def __init__(self) -> None:
        self.records: list[events_module.EventRecord] = []

    def emit(self, record: events_module.EventRecord) -> None:
        self.records.append(record)


def test_mood_crisis_blocks_and_skips_persistence_and_events():
    client = TestClient(app)
    fake_repo = FakeRepo()
    fake_emitter = FakeEmitter()
    app.dependency_overrides[repository_module.get_repository] = lambda: fake_repo
    app.dependency_overrides[events_module.get_event_emitter] = lambda: fake_emitter
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()

    response = client.post(
        "/mood",
        headers={"Authorization": "Bearer dev_test"},
        json={"valence": "negative", "intensity": "high", "free_text": "I want to kill myself"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["risk_level"] == 2
    assert body["crisis_action"] == "show_resources"
    assert fake_repo.saved_moods == 0
    assert fake_repo.upserts == 0
    assert fake_repo.mood_events == 1
    assert fake_emitter.records == []

    app.dependency_overrides.clear()
