from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.hold_reasons import HoldReason  # noqa: E402
from app import matching as matching_module  # noqa: E402
from app.matching import Candidate  # noqa: E402
from app import rate_limit as rate_limit_module  # noqa: E402


class InMemoryDedupeStore:
    def __init__(self):
        self.seen = set()

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"{sender_id}:{recipient_id}"
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


class InMemoryRateLimiter:
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


def _headers(token: str = "dev_test"):
    return {"Authorization": f"Bearer {token}"}


def _override_rate_limit():
    app.dependency_overrides[rate_limit_module.get_rate_limiter] = lambda: InMemoryRateLimiter()


def test_cold_start_triggers_hold_path():
    client = TestClient(app)
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    _override_rate_limit()

    payload = {
        "risk_level": 0,
        "intensity": "low",
        "themes": ["grief"],
        "candidates": [],
    }
    response = client.post("/match/simulate", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "HOLD"
    assert body["reason"] == HoldReason.INSUFFICIENT_POOL.value
    assert body["system_generated_empathy"]
    assert body["finite_content_bridge"]

    app.dependency_overrides.clear()


def test_risk_level_two_blocks():
    client = TestClient(app)
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    _override_rate_limit()

    payload = {
        "risk_level": 2,
        "intensity": "low",
        "themes": [],
        "candidates": [{"candidate_id": "c1", "intensity": "low", "themes": []}],
    }
    response = client.post("/match/simulate", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "CRISIS_BLOCK"
    assert body["crisis_action"] == "show_crisis"

    app.dependency_overrides.clear()


def test_cooldown_prevents_duplicate_targeting():
    client = TestClient(app)
    dedupe = InMemoryDedupeStore()
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: dedupe
    _override_rate_limit()

    payload = {
        "risk_level": 0,
        "intensity": "low",
        "themes": ["grief"],
        "candidates": [
            {"candidate_id": "c1", "intensity": "low", "themes": ["grief"]},
            {"candidate_id": "c2", "intensity": "low", "themes": ["grief"]},
            {"candidate_id": "c3", "intensity": "low", "themes": ["grief"]},
        ],
    }
    first = client.post("/match/simulate", json=payload, headers=_headers())
    assert first.status_code == 200
    assert first.json()["decision"] == "DELIVER"

    second = client.post("/match/simulate", json=payload, headers=_headers())
    assert second.status_code == 200
    assert second.json()["decision"] in {"DELIVER", "HOLD"}
    assert second.json()["reason"] in {"eligible", HoldReason.COOLDOWN_ACTIVE.value}

    app.dependency_overrides.clear()


def test_response_contains_no_identifiers():
    client = TestClient(app)
    app.dependency_overrides[matching_module.get_dedupe_store] = lambda: InMemoryDedupeStore()
    _override_rate_limit()

    payload = {
        "risk_level": 0,
        "intensity": "low",
        "themes": [],
        "candidates": [
            {"candidate_id": "candidate-secret", "intensity": "low", "themes": []},
            {"candidate_id": "other", "intensity": "low", "themes": []},
            {"candidate_id": "third", "intensity": "low", "themes": []},
        ],
    }
    response = client.post("/match/simulate", json=payload, headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert "recipient_id" not in body
    assert "candidate_id" not in body
    assert "sender_id" not in body

    app.dependency_overrides.clear()


def test_progressive_delivery_tightens_and_relaxes():
    dedupe = InMemoryDedupeStore()
    candidates = [
        Candidate(candidate_id="c1", intensity="high", themes=["other"]),
        Candidate(candidate_id="c2", intensity="medium", themes=["other"]),
        Candidate(candidate_id="c3", intensity="low", themes=["other"]),
    ]

    low_params = matching_module.progressive_params(0.1)
    low_decision = matching_module.match_decision(
        principal_id="sender",
        risk_level=0,
        intensity="low",
        themes=["calm"],
        candidates=candidates,
        dedupe_store=dedupe,
        intensity_band=low_params.intensity_band,
        allow_theme_relax=low_params.allow_theme_relax,
    )
    assert low_decision.decision == "HOLD"
    assert low_decision.reason == HoldReason.NO_ELIGIBLE_CANDIDATES.value

    high_params = matching_module.progressive_params(0.9)
    high_decision = matching_module.match_decision(
        principal_id="sender",
        risk_level=0,
        intensity="low",
        themes=["calm"],
        candidates=candidates,
        dedupe_store=dedupe,
        intensity_band=high_params.intensity_band,
        allow_theme_relax=high_params.allow_theme_relax,
    )
    assert high_decision.decision == "DELIVER"
