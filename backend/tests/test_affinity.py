from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta, timezone

from app.config import AFFINITY_DECAY_PER_DAY, AFFINITY_SCORE_MAX  # noqa: E402
from app.matching import Candidate, match_decision  # noqa: E402
from app.repository import InMemoryRepository, MessageRecord  # noqa: E402


class AllowAllDedupeStore:
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        return True


def test_positive_ack_updates_affinity_once():
    repo = InMemoryRepository()
    message_id = repo.save_message(
        MessageRecord(
            principal_id="sender",
            valence="neutral",
            intensity="low",
            emotion="calm",
            theme_tags=["calm"],
            risk_level=0,
            sanitized_text="safe",
            reid_risk=0.0,
        )
    )
    inbox_item_id = repo.create_inbox_item(message_id, "recipient", "safe")

    status = repo.acknowledge(inbox_item_id, "recipient", "helpful")
    assert status == "recorded"
    assert repo.get_affinity_map("sender")["calm"] == 1.0

    status_repeat = repo.acknowledge(inbox_item_id, "recipient", "helpful")
    assert status_repeat == "already_recorded"
    assert repo.get_affinity_map("sender")["calm"] == 1.0


def test_affinity_bias_prefers_higher_scored_theme():
    candidates = [
        Candidate(candidate_id="low_theme", intensity="low", themes=["sad"]),
        Candidate(candidate_id="high_theme", intensity="low", themes=["calm"]),
        Candidate(candidate_id="other_theme", intensity="low", themes=["other"]),
    ]
    decision = match_decision(
        principal_id="sender",
        risk_level=0,
        intensity="low",
        valence="neutral",
        themes=[],
        candidates=candidates,
        dedupe_store=AllowAllDedupeStore(),
        affinity_map={"calm": 5.0, "sad": 1.0},
    )
    assert decision.decision == "DELIVER"
    assert decision.recipient_id == "high_theme"


def test_affinity_decay_applies_over_days():
    repo = InMemoryRepository()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)
    repo.record_affinity("sender", "calm", 1.0, now=now)
    later = now + timedelta(days=2)
    decayed = repo.get_affinity_map("sender", now=later)["calm"]
    expected = 1.0 * (AFFINITY_DECAY_PER_DAY**2)
    assert abs(decayed - expected) < 1e-6


def test_affinity_score_is_bounded():
    repo = InMemoryRepository()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)
    repo.record_affinity("sender", "calm", AFFINITY_SCORE_MAX + 10, now=now)
    assert repo.get_affinity_map("sender", now=now)["calm"] == AFFINITY_SCORE_MAX
