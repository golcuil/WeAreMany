from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app import config as config_module  # noqa: E402
from app import security as security_module  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app.repository import MessageRecord  # noqa: E402


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def _override_deps(repo: repository_module.InMemoryRepository) -> TestClient:
    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    return TestClient(app)


def test_impact_counts_distinct_recipients(monkeypatch):
    monkeypatch.setenv("DEV_BEARER_TOKENS", "sender,other")
    config_module.DEV_BEARER_TOKENS = ["sender", "other"]
    security_module.DEV_BEARER_TOKENS = ["sender", "other"]
    repo = repository_module.InMemoryRepository()
    repo.messages["m1"] = MessageRecord(
        principal_id="dev:sender",
        valence="neutral",
        intensity="low",
        emotion=None,
        theme_tags=[],
        risk_level=0,
        sanitized_text="ok",
        reid_risk=0.1,
    )
    repo.messages["m2"] = MessageRecord(
        principal_id="dev:sender",
        valence="neutral",
        intensity="low",
        emotion=None,
        theme_tags=[],
        risk_level=0,
        sanitized_text="ok",
        reid_risk=0.1,
    )
    repo.messages["m3"] = MessageRecord(
        principal_id="dev:other",
        valence="neutral",
        intensity="low",
        emotion=None,
        theme_tags=[],
        risk_level=0,
        sanitized_text="ok",
        reid_risk=0.1,
    )
    repo.acks[("m1", "recipient1")] = "thanks"
    repo.acks[("m2", "recipient1")] = "helpful"
    repo.acks[("m2", "recipient2")] = "relate"
    repo.acks[("m2", "recipient3")] = "not_helpful"
    repo.acks[("m3", "recipient4")] = "helpful"

    client = _override_deps(repo)
    response = client.get("/impact", headers=_headers("sender"))
    assert response.status_code == 200
    assert response.json()["helped_count"] == 2

    other = client.get("/impact", headers=_headers("other"))
    assert other.status_code == 200
    assert other.json()["helped_count"] == 1

    app.dependency_overrides.clear()
