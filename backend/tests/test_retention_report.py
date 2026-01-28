import json
from datetime import datetime, timedelta, timezone

from app.repository import DailyAckAggregate, InMemoryRepository, SecurityEventRecord, SecondTouchEventRecord
from tools import retention_report


def _parse_payload(output: str) -> dict:
    prefix, payload = output.split(" ", 1)
    assert prefix == "retention_report"
    return json.loads(payload)


def test_retention_report_not_configured(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    exit_code = retention_report.main()
    output = capsys.readouterr().out.strip()
    payload = _parse_payload(output)
    assert exit_code == 0
    assert payload["status"] == "not_configured"
    assert payload["reason"] == "missing_dsn"


def test_retention_report_detects_drift(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=10)
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
            event_day_utc=old_time.date().isoformat(),
            event_type="send_held",
            reason="rate_limited",
            created_at=old_time,
        )
    )
    repo.second_touch_counters[(old_time.date().isoformat(), "offers_generated")] = 1
    repo.daily_ack_aggregates[(old_time.date().isoformat(), "theme")] = DailyAckAggregate(
        utc_day=old_time.date().isoformat(),
        theme_id="theme",
        delivered_count=1,
        positive_ack_count=0,
    )

    monkeypatch.setenv("POSTGRES_DSN", "postgres://user:pass@host/db")
    monkeypatch.setenv("SECURITY_EVENTS_RETENTION_DAYS", "1")
    monkeypatch.setenv("SECOND_TOUCH_EVENTS_RETENTION_DAYS", "1")
    monkeypatch.setenv("SECOND_TOUCH_AGG_RETENTION_DAYS", "1")
    monkeypatch.setenv("DAILY_ACK_RETENTION_DAYS", "1")
    monkeypatch.setattr(retention_report, "get_repository", lambda: repo)

    exit_code = retention_report.main()
    output = capsys.readouterr().out.strip()
    payload = _parse_payload(output)
    assert exit_code == 1
    assert payload["status"] == "fail"
    assert payload["reason"] == "ttl_drift"
    assert "postgres://user:pass@host/db" not in output
    assert "\n" not in output


def test_retention_report_ok(monkeypatch, capsys):
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    repo.security_events.append(
        SecurityEventRecord(
            actor_hash="hash",
            event_type="identity_leak_detected",
            meta={},
            created_at=now,
        )
    )
    repo.second_touch_events.append(
        SecondTouchEventRecord(
            event_day_utc=today,
            event_type="send_queued",
            reason=None,
            created_at=now,
        )
    )
    repo.second_touch_counters[(today, "offers_generated")] = 2
    repo.daily_ack_aggregates[(today, "theme")] = DailyAckAggregate(
        utc_day=today,
        theme_id="theme",
        delivered_count=2,
        positive_ack_count=1,
    )

    monkeypatch.setenv("POSTGRES_DSN", "postgres://user:pass@host/db")
    monkeypatch.setenv("SECURITY_EVENTS_RETENTION_DAYS", "30")
    monkeypatch.setenv("SECOND_TOUCH_EVENTS_RETENTION_DAYS", "30")
    monkeypatch.setenv("SECOND_TOUCH_AGG_RETENTION_DAYS", "30")
    monkeypatch.setenv("DAILY_ACK_RETENTION_DAYS", "30")
    monkeypatch.setattr(retention_report, "get_repository", lambda: repo)

    exit_code = retention_report.main()
    output = capsys.readouterr().out.strip()
    payload = _parse_payload(output)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["reason"] == "none"
