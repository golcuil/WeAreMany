from pathlib import Path
import sys
from datetime import datetime, timezone

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_recipient") -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_inbox_returns_empty_in_crisis_window():
    repo = repository_module.InMemoryRepository()
    principal_id = "dev:dev_recipient"
    repo.record_crisis_action(principal_id, "show_crisis_screen", now=datetime.now(timezone.utc))
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    client = TestClient(app)

    response = client.get("/inbox", headers=_headers())
    assert response.status_code == 200
    assert response.json()["items"] == []

    app.dependency_overrides.clear()
