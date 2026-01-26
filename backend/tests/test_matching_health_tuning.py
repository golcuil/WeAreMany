from datetime import datetime, timezone

from app.matching import default_matching_tuning
from app.matching_tuning import tune_matching
from app.repository import InMemoryRepository, InboxItemRecord, MessageRecord


def test_global_matching_health_ratio():
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)
    message_id = "msg-1"
    repo.messages[message_id] = MessageRecord(
        principal_id="sender-a",
        valence="neutral",
        intensity="low",
        emotion=None,
        theme_tags=[],
        risk_level=0,
        sanitized_text="hello",
        reid_risk=0.0,
    )
    repo.inbox_items["inbox-1"] = InboxItemRecord(
        inbox_item_id="inbox-1",
        message_id=message_id,
        recipient_id="recipient-a",
        text="hello",
        created_at=now.isoformat(),
        state="unread",
        ack_status=None,
    )
    repo.acks[(message_id, "recipient-a")] = "thanks"

    health = repo.get_global_matching_health(window_days=7)
    assert health.delivered_count == 1
    assert health.positive_ack_count == 1
    assert health.ratio == 1.0


def test_global_matching_health_handles_zero_deliveries():
    repo = InMemoryRepository()
    health = repo.get_global_matching_health(window_days=7)
    assert health.delivered_count == 0
    assert health.positive_ack_count == 0
    assert health.ratio == 0.0


def test_tuning_tightens_on_low_health():
    tuning = default_matching_tuning()
    updated = tune_matching(0.1, tuning)
    assert updated.high_intensity_band <= tuning.high_intensity_band
    assert updated.pool_multiplier_low <= tuning.pool_multiplier_low
    assert updated.allow_theme_relax_high is False


def test_tuning_relaxes_on_high_health():
    tuning = default_matching_tuning()
    updated = tune_matching(0.7, tuning)
    assert updated.high_intensity_band >= tuning.high_intensity_band
    assert updated.pool_multiplier_high >= tuning.pool_multiplier_high
    assert updated.allow_theme_relax_high is True


def test_tuning_no_change_on_neutral_health():
    tuning = default_matching_tuning()
    updated = tune_matching(0.4, tuning)
    assert updated == tuning
