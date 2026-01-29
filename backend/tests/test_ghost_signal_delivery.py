import os
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

from app.repository import (
    PostgresRepository,
    _hash_affinity_actor,
    _hash_notification_intent_key,
    _is_silent_hours,
    _next_local_morning,
)


POSTGRES_DSN = os.getenv("POSTGRES_DSN_TEST")


@pytest.mark.skipif(POSTGRES_DSN is None or psycopg is None, reason="POSTGRES_DSN_TEST not set")
def test_deliver_pending_messages_skip_locked_prevents_double_delivery():
    repo = PostgresRepository(POSTGRES_DSN)
    recipient_id = "r1"
    sender_id = "s1"
    message_id = None
    now = datetime.now(timezone.utc)

    with psycopg.connect(POSTGRES_DSN) as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM inbox_items WHERE recipient_device_id = %s",
            (recipient_id,),
        )
        cur.execute(
            "DELETE FROM notification_intents WHERE recipient_hash = %s",
            (_hash_affinity_actor(recipient_id),),
        )
        cur.execute(
            "DELETE FROM messages WHERE origin_device_id = %s",
            (sender_id,),
        )
        cur.execute(
            "DELETE FROM principal_crisis_state WHERE principal_id = %s",
            (recipient_id,),
        )
        cur.execute(
            "DELETE FROM eligible_principals WHERE principal_id = %s",
            (recipient_id,),
        )
        cur.execute(
            "INSERT INTO eligible_principals (principal_id, intensity_bucket, theme_tags, last_active_bucket, updated_at)"
            " VALUES (%s, %s, %s, date_trunc('hour', now()), now())",
            (recipient_id, "low", []),
        )
        cur.execute(
            """
            INSERT INTO messages
            (valence, intensity, emotion, theme_tags, risk_level, sanitized_text, reid_risk, identity_leak,
             status, origin_device_id, recipient_device_id, deliver_at, delivery_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                "positive",
                "low",
                "calm",
                [],
                0,
                "hello",
                0.0,
                False,
                "queued",
                sender_id,
                recipient_id,
                now - timedelta(minutes=1),
                "pending",
            ),
        )
        message_id = str(cur.fetchone()[0])

    def _deliver():
        return repo.deliver_pending_messages(now, batch_size=1, default_tz_offset_minutes=0)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: _deliver(), range(2)))

    assert sum(results) == 1

    with psycopg.connect(POSTGRES_DSN) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM inbox_items WHERE message_id = %s",
            (message_id,),
        )
        inbox_count = cur.fetchone()[0]
        cur.execute(
            "SELECT delivery_status FROM messages WHERE id = %s",
            (message_id,),
        )
        status = cur.fetchone()[0]
        intent_key = _hash_notification_intent_key(message_id)
        cur.execute(
            "SELECT COUNT(*) FROM notification_intents WHERE intent_key = %s",
            (intent_key,),
        )
        intents_count = cur.fetchone()[0]

    assert inbox_count == 1
    assert intents_count == 1
    assert status == "delivered"


def test_hash_notification_intent_key_is_stable_and_unique():
    first = _hash_notification_intent_key("m1")
    second = _hash_notification_intent_key("m2")
    assert first == _hash_notification_intent_key("m1")
    assert first != second


def test_next_local_morning_edge_cases():
    now_early = datetime(2026, 1, 1, 21, 59, tzinfo=timezone.utc)
    now_late = datetime(2026, 1, 1, 22, 1, tzinfo=timezone.utc)
    assert _is_silent_hours(now_early, 0) is False
    assert _is_silent_hours(now_late, 0) is True
    next_morning = _next_local_morning(now_late, 0)
    assert next_morning.hour == 9
    assert next_morning.date() == (now_late + timedelta(days=1)).date()
