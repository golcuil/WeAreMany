from app.config import AFFINITY_MAX_BIAS, AFFINITY_SCALE
from app.matching import Candidate, _affinity_weight, match_decision


class AllowAllDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def test_affinity_bias_is_bounded():
    assert AFFINITY_MAX_BIAS <= 0.10
    candidate = Candidate(candidate_id="c1", intensity="low", themes=["calm"])
    weight = _affinity_weight(candidate, {"calm": 100.0}, 100.0)
    assert weight <= 1.0 + AFFINITY_MAX_BIAS
    assert weight >= 1.0


def test_affinity_scale_is_small():
    assert AFFINITY_SCALE <= 0.10


def test_affinity_not_applied_on_hold():
    candidates = [
        Candidate(candidate_id="c1", intensity="low", themes=["calm"]),
    ]
    decision = match_decision(
        principal_id="sender",
        risk_level=0,
        intensity="low",
        valence="neutral",
        themes=["calm"],
        candidates=candidates[:1],
        dedupe_store=AllowAllDedupeStore(),
        affinity_map={"calm": 100.0},
    )
    assert decision.decision != "DELIVER"
