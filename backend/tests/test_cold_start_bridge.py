from pathlib import Path
import re
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.hold_reasons import HoldReason  # noqa: E402
from app import moderation as moderation_module  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


class InMemoryDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_sender") -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_cold_start_returns_system_message():
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
        json={"valence": "neutral", "intensity": "low", "free_text": "hello"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "held"
    assert body["hold_reason"] == HoldReason.INSUFFICIENT_POOL.value

    inbox_items = list(repo.inbox_items.values())
    assert len(inbox_items) == 1
    assert inbox_items[0].recipient_id == "sender"

    system_messages = [record for record in repo.messages.values() if record.principal_id == "system"]
    assert len(system_messages) == 1
    system_text = system_messages[0].sanitized_text or ""
    assert system_text
    assert "hello" not in system_text
    assert "real person" not in system_text
    assert "written by" not in system_text
    assert not re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", system_text, re.IGNORECASE)
    assert not re.search(r"\+?\d[\d\s().-]{7,}\d", system_text)

    assert any(tag.startswith("content:") for tag in system_messages[0].theme_tags)

    app.dependency_overrides.clear()
