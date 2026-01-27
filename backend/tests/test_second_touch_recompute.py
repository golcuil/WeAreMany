from datetime import datetime, timedelta, timezone

from app.repository import InMemoryRepository
from tools.recompute_second_touch_aggregates import main as recompute_main


def test_recompute_overwrites_only_known_keys(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)

    day_a = (now - timedelta(days=1)).date().isoformat()
    day_b = now.date().isoformat()

    repo.increment_second_touch_counter(day_a, "offers_generated")
    repo.increment_second_touch_counter(day_b, "sends_queued")
    repo.increment_second_touch_counter(day_b, "offers_suppressed_rate_limited")
    repo.increment_second_touch_counter(day_b, "sends_held_cooldown_active")
    repo.increment_second_touch_counter(day_b, "disables_identity_leak")

    repo.second_touch_counters[(day_a, "offers_generated")] = 10
    repo.second_touch_counters[(day_b, "sends_queued")] = 5
    repo.second_touch_counters[(day_b, "offers_suppressed_rate_limited")] = 2
    repo.second_touch_counters[(day_b, "sends_held_cooldown_active")] = 3
    repo.second_touch_counters[(day_b, "disables_identity_leak")] = 4

    result = repo.recompute_second_touch_daily_aggregates(
        (now - timedelta(days=1)).date(), now.date()
    )

    assert result["recompute_partial"] is False
    assert result["reason"] is None
    assert (
        repo.second_touch_counters[(day_a, "offers_generated")] == 1
    )
    assert repo.second_touch_counters[(day_b, "sends_queued")] == 1
    assert repo.second_touch_counters[(day_b, "offers_suppressed_rate_limited")] == 1
    assert repo.second_touch_counters[(day_b, "sends_held_cooldown_active")] == 1
    assert repo.second_touch_counters[(day_b, "disables_identity_leak")] == 1

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
