from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def test_reflection_summary_returns_distribution_trend_and_volatility():
    repo = repository_module.InMemoryRepository()
    now = datetime.now(timezone.utc)
    events = [
        repository_module.MoodEventRecord(
            principal_id="test",
            created_at=now - timedelta(days=6),
            valence="positive",
            intensity="low",
            expressed_emotion="calm",
            risk_level=0,
            theme_tag="calm",
        ),
        repository_module.MoodEventRecord(
            principal_id="test",
            created_at=now - timedelta(days=3),
            valence="neutral",
            intensity="medium",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        ),
        repository_module.MoodEventRecord(
            principal_id="test",
            created_at=now - timedelta(days=1),
            valence="negative",
            intensity="high",
            expressed_emotion="sad",
            risk_level=0,
            theme_tag="grief",
        ),
    ]
    for event in events:
        repo.record_mood_event(event)

    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = (
        lambda: InMemoryRateLimiter()
    )

    client = TestClient(app)
    response = client.get(
        "/reflection/summary?window_days=7",
        headers={"Authorization": "Bearer dev_test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["window_days"] == 7
    assert body["total_entries"] == 3
    assert body["distribution"] == {"calm": 1, "sad": 2}
    assert body["trend"] == "down"
    assert body["volatility_days"] == 2

    app.dependency_overrides.clear()
