from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import repository as repository_module  # noqa: E402
from tools.cleanup_second_touch_aggregates import main as cleanup_main  # noqa: E402


def test_inmemory_second_touch_cleanup_removes_old_days():
    repo = repository_module.InMemoryRepository()
    now = datetime(2026, 1, 27, tzinfo=timezone.utc)
    old_day = (now - timedelta(days=200)).date().isoformat()
    recent_day = (now - timedelta(days=10)).date().isoformat()
    repo.increment_second_touch_counter(old_day, "offers_generated", 3)
    repo.increment_second_touch_counter(recent_day, "offers_generated", 2)

    deleted = repo.cleanup_second_touch_daily_aggregates(180, now)
    assert deleted == 1
    counters = repo.get_second_touch_counters(365)
    assert counters.get("offers_generated") == 2


def test_cleanup_tool_output_is_aggregate_only(monkeypatch, capsys):
    repo = repository_module.InMemoryRepository()
    now = datetime(2026, 1, 27, tzinfo=timezone.utc)
    repo.increment_second_touch_counter(now.date().isoformat(), "offers_generated", 1)
    monkeypatch.setattr(repository_module, "get_repository", lambda: repo)
    monkeypatch.setattr(
        "tools.cleanup_second_touch_aggregates.datetime",
        type("FixedDatetime", (), {"now": staticmethod(lambda tz=None: now)}),
    )

    exit_code = cleanup_main(["--retention-days", "180"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output.startswith("second_touch_cleanup")
    assert "offer_id" not in output
    assert "recipient" not in output
    assert "principal" not in output
