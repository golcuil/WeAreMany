from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import main as main_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


def _headers(token: str = "dev_user") -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_similar_count_respects_k_anon():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id="a",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="low",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        )
    )
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id="b",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="low",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        )
    )
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id="c",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="low",
            expressed_emotion="sad",
            risk_level=2,
            theme_tag="grief",
        )
    )
    assert repo.get_similar_count("a", "grief", "negative", window_days=7) == 1


def test_mood_response_includes_similar_count_when_threshold_met():
    previous_k = main_module.K_ANON_MIN
    main_module.K_ANON_MIN = 2
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id="user_a",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="low",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        )
    )
    repo.record_mood_event(
        repository_module.MoodEventRecord(
            principal_id="user_b",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="low",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        )
    )
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    client = TestClient(app)

    response = client.post(
        "/mood",
        headers=_headers("dev_user"),
        json={"valence": "negative", "intensity": "low", "emotion": "sad"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["similar_count"] == 2

    main_module.K_ANON_MIN = previous_k
    app.dependency_overrides.clear()
