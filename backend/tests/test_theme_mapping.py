from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app.themes import CANONICAL_THEMES, map_mood_to_themes, normalize_theme_tags  # noqa: E402


def _headers(token: str = "dev_theme"):
    return {"Authorization": f"Bearer {token}"}


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def test_theme_mapper_is_deterministic_and_canonical():
    first = map_mood_to_themes("sad", "negative", "low")
    second = map_mood_to_themes("sad", "negative", "low")
    assert first == second
    assert 1 <= len(first) <= 3
    assert all(tag in CANONICAL_THEMES for tag in first)


def test_normalize_theme_tags_filters_to_canonical():
    normalized = normalize_theme_tags(["grief", "unknown", "grief", "hope"])
    assert normalized == ["grief", "calm", "hope"]


def test_message_stores_normalized_theme_tags():
    repo = repository_module.InMemoryRepository()
    repo.get_or_create_finite_content = lambda *args, **kwargs: "content-1"
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    client = TestClient(app)

    response = client.post(
        "/messages",
        headers=_headers(),
        json={
            "valence": "negative",
            "intensity": "low",
            "emotion": "sad",
            "free_text": "hello",
        },
    )
    assert response.status_code == 200
    message = next(iter(repo.messages.values()))
    assert message.theme_tags == map_mood_to_themes("sad", "negative", "low")

    app.dependency_overrides.clear()
