from datetime import datetime, timedelta, timezone

from app.repository import InMemoryRepository
from tools.recompute_second_touch_aggregates import main as recompute_main


def test_recompute_overwrites_only_known_keys(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)

    offer_id = repo.create_second_touch_offer("recipient", "sender")
    offer = repo.second_touch_offers[offer_id]
    offer.created_at = now - timedelta(days=1)
    offer.used_at = now

    repo.second_touch_counters[(offer.created_at.date().isoformat(), "offers_generated")] = 10
    repo.second_touch_counters[(now.date().isoformat(), "sends_queued")] = 5
    repo.second_touch_counters[(now.date().isoformat(), "offers_suppressed_rate_limited")] = 2

    result = repo.recompute_second_touch_daily_aggregates(
        (now - timedelta(days=1)).date(), now.date()
    )

    assert result["recompute_partial"] is True
    assert result["reason"] == "missing_source_events"
    assert (
        repo.second_touch_counters[
            (offer.created_at.date().isoformat(), "offers_generated")
        ]
        == 1
    )
    assert repo.second_touch_counters[(now.date().isoformat(), "sends_queued")] == 1
    assert (
        repo.second_touch_counters[
            (now.date().isoformat(), "offers_suppressed_rate_limited")
        ]
        == 2
    )

    monkeypatch.setattr(
        "tools.recompute_second_touch_aggregates.get_repository",
        lambda: repo,
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr("tools.recompute_second_touch_aggregates.datetime", FixedDateTime)
    exit_code = recompute_main(["--days", "2"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output.startswith("second_touch_recompute")
