from datetime import datetime, timedelta, timezone

from app.repository import InMemoryRepository, SecondTouchEventRecord
from tools.cleanup_second_touch_events import main as cleanup_main


def test_second_touch_events_cleanup(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)
    old = now - timedelta(days=100)

    repo.second_touch_events.append(
        SecondTouchEventRecord(
            event_day_utc=old.date().isoformat(),
            event_type="offer_generated",
            reason=None,
            created_at=old,
        )
    )
    repo.second_touch_events.append(
        SecondTouchEventRecord(
            event_day_utc=now.date().isoformat(),
            event_type="send_queued",
            reason=None,
            created_at=now,
        )
    )

    monkeypatch.setattr(
        "tools.cleanup_second_touch_events.get_repository",
        lambda: repo,
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr("tools.cleanup_second_touch_events.datetime", FixedDateTime)
    exit_code = cleanup_main(["--retention-days", "30"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output.startswith("second_touch_events_cleanup")
    assert len(repo.second_touch_events) == 1
