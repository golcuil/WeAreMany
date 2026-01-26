from datetime import datetime, timedelta, timezone
import os

import pytest

from app.repository import InMemoryRepository, PostgresRepository, SecurityEventRecord, psycopg

POSTGRES_DSN = os.getenv("POSTGRES_DSN_TEST")


def _record(repo, actor_hash: str, event_type: str, created_at: datetime) -> None:
    repo.record_security_event(
        SecurityEventRecord(
            actor_hash=actor_hash,
            event_type=event_type,
            meta={},
            created_at=created_at,
        )
    )


def test_in_memory_prunes_old_events(monkeypatch):
    repo = InMemoryRepository()
    now = datetime(2026, 1, 30, tzinfo=timezone.utc)
    old = now - timedelta(days=31)
    recent = now - timedelta(days=5)
    _record(repo, "a", "identity_leak_detected", old)
    _record(repo, "b", "identity_leak_detected", recent)

    deleted = repo.prune_security_events(now, retention_days=30)
    assert deleted == 1
    assert len(repo.security_events) == 1
    assert repo.security_events[0].actor_hash == "b"


def test_in_memory_prune_respects_config(monkeypatch):
    from app import config as config_module

    repo = InMemoryRepository()
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    old = now - timedelta(days=2)
    recent = now - timedelta(hours=12)
    _record(repo, "a", "identity_leak_detected", old)
    _record(repo, "b", "identity_leak_detected", recent)

    monkeypatch.setattr(config_module, "SECURITY_EVENTS_RETENTION_DAYS", 1)
    deleted = repo.prune_security_events(now)
    assert deleted == 1
    assert len(repo.security_events) == 1
    assert repo.security_events[0].actor_hash == "b"


@pytest.mark.skipif(POSTGRES_DSN is None or psycopg is None, reason="POSTGRES_DSN_TEST not set")
def test_postgres_prune_security_events():
    repo = PostgresRepository(POSTGRES_DSN)
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=40)
    recent = now - timedelta(days=5)
    _record(repo, "pg-old", "identity_leak_detected", old)
    _record(repo, "pg-recent", "identity_leak_detected", recent)

    deleted = repo.prune_security_events(now, retention_days=30)
    assert deleted >= 1

    with repo._conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM security_events WHERE actor_hash = %s", ("pg-old",))
        old_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM security_events WHERE actor_hash = %s", ("pg-recent",))
        recent_count = cur.fetchone()[0]

    assert old_count == 0
    assert recent_count >= 1
