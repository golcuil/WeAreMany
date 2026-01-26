from datetime import datetime, timezone
import os

import pytest

from app.repository import (
    DailyAckAggregate,
    InMemoryRepository,
    MessageRecord,
    PostgresRepository,
    psycopg,
)

POSTGRES_DSN = os.getenv("POSTGRES_DSN_TEST")


def _build_message(theme_id: str) -> MessageRecord:
    return MessageRecord(
        principal_id="sender",
        valence="neutral",
        intensity="low",
        emotion=None,
        theme_tags=[theme_id],
        risk_level=0,
        sanitized_text="hello",
        reid_risk=0.0,
    )


def test_in_memory_daily_aggregates_deliver_and_ack():
    repo = InMemoryRepository()
    message_id = repo.save_message(_build_message("calm"))
    inbox_item_id = repo.create_inbox_item(message_id, "recipient", "hello")
    day_key = datetime.now(timezone.utc).date().isoformat()

    aggregates = repo.list_daily_ack_aggregates(7, theme_id="calm")
    assert len(aggregates) == 1
    record = aggregates[0]
    assert record.utc_day == day_key
    assert record.delivered_count == 1
    assert record.positive_ack_count == 0

    repo.acknowledge(inbox_item_id, "recipient", "helpful")
    aggregates = repo.list_daily_ack_aggregates(7, theme_id="calm")
    assert aggregates[0].positive_ack_count == 1


@pytest.mark.skipif(POSTGRES_DSN is None or psycopg is None, reason="POSTGRES_DSN_TEST not set")
def test_postgres_daily_aggregates_deliver_and_ack():
    repo = PostgresRepository(POSTGRES_DSN)
    day_key = datetime.now(timezone.utc).date().isoformat()
    theme_id = "test-theme-agg"

    with repo._conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM daily_ack_aggregates WHERE theme_id = %s", (theme_id,))

    message_id = repo.save_message(_build_message(theme_id))
    inbox_item_id = repo.create_inbox_item(message_id, "recipient", "hello")
    repo.acknowledge(inbox_item_id, "recipient", "thanks")

    aggregates = repo.list_daily_ack_aggregates(7, theme_id=theme_id)
    assert len(aggregates) >= 1
    record = aggregates[0]
    assert record.utc_day == day_key
    assert record.delivered_count >= 1
    assert record.positive_ack_count >= 1
