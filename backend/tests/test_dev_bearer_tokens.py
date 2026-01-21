import importlib
from pathlib import Path
import sys
from typing import Optional

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import moderation as moderation_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app import repository as repository_module  # noqa: E402


class InMemoryLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class InMemoryLeakThrottle:
    def check_and_increment(self, principal_id: str) -> None:
        return None


def _load_app(monkeypatch: pytest.MonkeyPatch, dev_tokens: Optional[str]):
    if dev_tokens is None:
        monkeypatch.delenv("DEV_BEARER_TOKENS", raising=False)
    else:
        monkeypatch.setenv("DEV_BEARER_TOKENS", dev_tokens)

    from app import config as config_module  # noqa: E402
    from app import security as security_module  # noqa: E402
    from app import main as main_module  # noqa: E402

    importlib.reload(config_module)
    importlib.reload(security_module)
    importlib.reload(main_module)
    return main_module.app


def _mood_payload() -> dict:
    return {"valence": "positive", "intensity": "low"}


def test_dev_bearer_token_accepts_allowlisted_token(monkeypatch: pytest.MonkeyPatch):
    app = _load_app(monkeypatch, "tokenA,tokenB")
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[repository_module.get_repository] = (
        lambda: repository_module.InMemoryRepository()
    )

    client = TestClient(app)
    response = client.post(
        "/mood",
        headers={"Authorization": "Bearer tokenA"},
        json=_mood_payload(),
    )
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_dev_bearer_token_rejected_without_allowlist(monkeypatch: pytest.MonkeyPatch):
    app = _load_app(monkeypatch, None)
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryLimiter()
    app.dependency_overrides[moderation_module.get_leak_throttle] = lambda: InMemoryLeakThrottle()
    app.dependency_overrides[repository_module.get_repository] = (
        lambda: repository_module.InMemoryRepository()
    )

    client = TestClient(app)
    response = client.post(
        "/mood",
        headers={"Authorization": "Bearer tokenA"},
        json=_mood_payload(),
    )
    assert response.status_code == 401

    app.dependency_overrides.clear()
