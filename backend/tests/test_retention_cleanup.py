from datetime import datetime, timedelta, timezone

from app.repository import DailyAckAggregate, InMemoryRepository, SecurityEventRecord, SecondTouchEventRecord
from tools import retention_cleanup


def test_retention_cleanup_inmemory(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=10)
    old_day = old_time.date().isoformat()
    repo.security_events.append(
        SecurityEventRecord(
            actor_hash="hash",
            event_type="identity_leak_detected",
            meta={},
            created_at=old_time,
        )
    )
    repo.second_touch_events.append(
        SecondTouchEventRecord(
            event_day_utc=old_day,
            event_type="send_held",
            reason="rate_limited",
            created_at=old_time,
        )
    )
    repo.second_touch_counters[(old_day, "offers_generated")] = 1
    repo.daily_ack_aggregates[(old_day, "theme")] = DailyAckAggregate(
        utc_day=old_day,
        theme_id="theme",
        delivered_count=1,
        positive_ack_count=0,
    )

    monkeypatch.setenv("SECURITY_EVENTS_RETENTION_DAYS", "1")
    monkeypatch.setenv("SECOND_TOUCH_EVENTS_RETENTION_DAYS", "1")
    monkeypatch.setenv("SECOND_TOUCH_AGG_RETENTION_DAYS", "1")
    monkeypatch.setenv("DAILY_ACK_RETENTION_DAYS", "1")
    monkeypatch.setattr(retention_cleanup, "get_repository", lambda: repo)

    exit_code = retention_cleanup.main()
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert "postgres://" not in output
    assert len(repo.security_events) == 0
    assert len(repo.second_touch_events) == 0
    assert len(repo.second_touch_counters) == 0
    assert len(repo.daily_ack_aggregates) == 0
