from dataclasses import dataclass
from typing import List, Optional, Protocol

import os

from .matching import Candidate

try:
    import psycopg
except Exception:  # pragma: no cover - optional dependency at runtime
    psycopg = None


@dataclass
class MoodRecord:
    principal_id: str
    valence: str
    intensity: str
    emotion: Optional[str]
    risk_level: int
    sanitized_text: Optional[str]


@dataclass
class MessageRecord:
    principal_id: str
    valence: str
    intensity: str
    emotion: Optional[str]
    risk_level: int
    sanitized_text: Optional[str]
    reid_risk: float


@dataclass
class InboxItemRecord:
    inbox_item_id: str
    message_id: str
    recipient_id: str
    text: str
    created_at: str
    state: str
    ack_status: Optional[str]


class Repository(Protocol):
    def save_mood(self, record: MoodRecord) -> None:
        ...

    def save_message(self, record: MessageRecord) -> str:
        ...

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        ...

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        ...

    def acknowledge(self, inbox_item_id: str, recipient_id: str, reaction: str) -> str:
        ...

    def get_candidate_pool(self, sender_id: str, intensity: str, themes: List[str]) -> List[Candidate]:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self.messages = {}
        self.inbox_items = {}
        self.acks = {}
        self.candidate_pool: List[Candidate] = []

    def save_mood(self, record: MoodRecord) -> None:
        return None

    def save_message(self, record: MessageRecord) -> str:
        message_id = _new_uuid()
        self.messages[message_id] = record
        return message_id

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        inbox_item_id = _new_uuid()
        self.inbox_items[inbox_item_id] = InboxItemRecord(
            inbox_item_id=inbox_item_id,
            message_id=message_id,
            recipient_id=recipient_id,
            text=text,
            created_at="",
            state="unread",
            ack_status=None,
        )
        return inbox_item_id

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        items = [item for item in self.inbox_items.values() if item.recipient_id == recipient_id]
        for item in items:
            ack_key = (item.message_id, recipient_id)
            if ack_key in self.acks:
                item.ack_status = self.acks[ack_key]
                item.state = "responded"
        return items

    def acknowledge(self, inbox_item_id: str, recipient_id: str, reaction: str) -> str:
        item = self.inbox_items.get(inbox_item_id)
        if not item or item.recipient_id != recipient_id:
            raise PermissionError("forbidden")
        ack_key = (item.message_id, recipient_id)
        self.acks[ack_key] = reaction
        item.state = "responded"
        item.ack_status = reaction
        return "recorded"

    def get_candidate_pool(self, sender_id: str, intensity: str, themes: List[str]) -> List[Candidate]:
        return list(self.candidate_pool)


class PostgresRepository:
    def __init__(self, dsn: str) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgresRepository")
        self._dsn = dsn

    def _conn(self):
        return psycopg.connect(self._dsn)

    def save_mood(self, record: MoodRecord) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mood_submissions
                (device_id, valence, intensity, emotion, risk_level, sanitized_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    record.principal_id,
                    record.valence,
                    record.intensity,
                    record.emotion,
                    record.risk_level,
                    record.sanitized_text,
                ),
            )

    def save_message(self, record: MessageRecord) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                (valence, intensity, emotion, risk_level, sanitized_text, reid_risk, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    record.valence,
                    record.intensity,
                    record.emotion,
                    record.risk_level,
                    record.sanitized_text,
                    record.reid_risk,
                    "queued",
                ),
            )
            return str(cur.fetchone()[0])

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inbox_items
                (message_id, recipient_device_id, state)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (message_id, recipient_id, "unread"),
            )
            return str(cur.fetchone()[0])

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT i.id, i.message_id, i.recipient_device_id, i.state, i.received_at,
                       m.sanitized_text,
                       a.reaction
                FROM inbox_items i
                JOIN messages m ON m.id = i.message_id
                LEFT JOIN acknowledgements a
                  ON a.message_id = i.message_id AND a.recipient_device_id = i.recipient_device_id
                WHERE i.recipient_device_id = %s
                ORDER BY i.received_at DESC
                """,
                (recipient_id,),
            )
            rows = cur.fetchall()
        items: List[InboxItemRecord] = []
        for row in rows:
            items.append(
                InboxItemRecord(
                    inbox_item_id=str(row[0]),
                    message_id=str(row[1]),
                    recipient_id=row[2],
                    state=row[3],
                    created_at=row[4].isoformat(),
                    text=row[5] or "",
                    ack_status=row[6],
                )
            )
        return items

    def acknowledge(self, inbox_item_id: str, recipient_id: str, reaction: str) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_id, recipient_device_id
                FROM inbox_items
                WHERE id = %s
                """,
                (inbox_item_id,),
            )
            row = cur.fetchone()
            if not row or row[1] != recipient_id:
                raise PermissionError("forbidden")
            message_id = row[0]
            cur.execute(
                """
                INSERT INTO acknowledgements (message_id, recipient_device_id, reaction)
                VALUES (%s, %s, %s)
                ON CONFLICT (message_id, recipient_device_id)
                DO UPDATE SET reaction = EXCLUDED.reaction
                """,
                (message_id, recipient_id, reaction),
            )
        return "recorded"

    def get_candidate_pool(self, sender_id: str, intensity: str, themes: List[str]) -> List[Candidate]:
        return []


_default_repo = InMemoryRepository()


def get_repository() -> Repository:
    dsn = os.getenv("POSTGRES_DSN")
    if dsn:
        return PostgresRepository(dsn)
    return _default_repo


def _new_uuid() -> str:
    import uuid

    return str(uuid.uuid4())
