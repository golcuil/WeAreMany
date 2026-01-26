from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.bridge import SYSTEM_SENDER_ID  # noqa: E402
from app.inbox_origin import InboxOrigin  # noqa: E402
from app import repository as repository_module  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402
from app.security import _verify_token  # noqa: E402


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_recipient") -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_inbox_origin_system_and_peer():
    repo = repository_module.InMemoryRepository()
    system_message = repo.save_message(
        repository_module.MessageRecord(
            principal_id=SYSTEM_SENDER_ID,
            valence="neutral",
            intensity="low",
            emotion=None,
            theme_tags=[],
            risk_level=0,
            sanitized_text="system",
            reid_risk=0.0,
        )
    )
    peer_message = repo.save_message(
        repository_module.MessageRecord(
            principal_id="sender",
            valence="neutral",
            intensity="low",
            emotion=None,
            theme_tags=[],
            risk_level=0,
            sanitized_text="peer",
            reid_risk=0.0,
        )
    )
    repo.create_inbox_item(system_message, "recipient", "system")
    repo.create_inbox_item(peer_message, "recipient", "peer")

    items = repo.list_inbox_items("recipient")
    origins = {item.text: item.origin for item in items}
    assert origins["system"] == InboxOrigin.SYSTEM.value
    assert origins["peer"] == InboxOrigin.PEER.value


def test_inbox_response_does_not_expose_origin():
    repo = repository_module.InMemoryRepository()
    principal_id = _verify_token("dev_recipient").principal_id
    message_id = repo.save_message(
        repository_module.MessageRecord(
            principal_id=SYSTEM_SENDER_ID,
            valence="neutral",
            intensity="low",
            emotion=None,
            theme_tags=[],
            risk_level=0,
            sanitized_text="system",
            reid_risk=0.0,
        )
    )
    repo.create_inbox_item(message_id, principal_id, "system")

    app.dependency_overrides[repository_module.get_repository] = lambda: repo
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()
    client = TestClient(app)
    response = client.get("/inbox", headers=_headers("dev_recipient"))
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert "origin" not in items[0]

    app.dependency_overrides.clear()
