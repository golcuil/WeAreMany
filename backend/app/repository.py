from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Protocol

import os

from .matching import Candidate
from .config import ELIGIBLE_RECENCY_HOURS, MATCH_SAMPLE_LIMIT

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
class MoodEventRecord:
    principal_id: str
    created_at: datetime
    valence: str
    intensity: str
    expressed_emotion: Optional[str]
    risk_level: int
    theme_tag: Optional[str] = None


@dataclass
class ReflectionSummary:
    window_days: int
    total_entries: int
    distribution: Dict[str, int]
    trend: str
    volatility_days: int


@dataclass(frozen=True)
class MatchingHealth:
    delivered_count: int
    positive_ack_count: int
    ratio: float


@dataclass
class MessageRecord:
    principal_id: str
    valence: str
    intensity: str
    emotion: Optional[str]
    theme_tags: List[str]
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

    def record_mood_event(self, record: MoodEventRecord) -> None:
        ...

    def get_reflection_summary(self, principal_id: str, window_days: int) -> ReflectionSummary:
        ...

    def save_message(self, record: MessageRecord) -> str:
        ...

    def upsert_eligible_principal(
        self,
        principal_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
    ) -> None:
        ...

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str) -> None:
        ...

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        ...

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        ...

    def acknowledge(self, inbox_item_id: str, recipient_id: str, reaction: str) -> str:
        ...

    def get_helped_count(self, principal_id: str) -> int:
        ...

    def record_affinity(self, sender_id: str, theme_id: str, delta: float) -> None:
        ...

    def get_affinity_map(self, sender_id: str) -> Dict[str, float]:
        ...

    def get_eligible_candidates(
        self,
        sender_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
        limit: int = MATCH_SAMPLE_LIMIT,
    ) -> List[Candidate]:
        ...

    def get_matching_health(self, principal_id: str, window_days: int = 7) -> MatchingHealth:
        ...

    def get_similar_count(
        self,
        principal_id: str,
        theme_tag: str,
        valence: str,
        window_days: int,
    ) -> int:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self.messages = {}
        self.inbox_items = {}
        self.acks = {}
        self.eligible_principals = {}
        self.candidate_pool: List[Candidate] = []
        self.mood_events: List[MoodEventRecord] = []
        self.affinity_scores: Dict[str, Dict[str, float]] = {}

    def save_mood(self, record: MoodRecord) -> None:
        return None

    def record_mood_event(self, record: MoodEventRecord) -> None:
        self.mood_events.append(record)

    def get_reflection_summary(self, principal_id: str, window_days: int) -> ReflectionSummary:
        records = _filter_mood_events(self.mood_events, principal_id, window_days)
        return _summarize_mood_events(records, window_days)

    def get_similar_count(
        self,
        principal_id: str,
        theme_tag: str,
        valence: str,
        window_days: int,
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        principals = set()
        for record in self.mood_events:
            if record.risk_level == 2:
                continue
            if record.created_at < cutoff:
                continue
            if record.principal_id == principal_id:
                continue
            if record.theme_tag != theme_tag:
                continue
            if record.valence != valence:
                continue
            principals.add(record.principal_id)
        return len(principals)

    def save_message(self, record: MessageRecord) -> str:
        message_id = _new_uuid()
        self.messages[message_id] = record
        return message_id

    def upsert_eligible_principal(
        self,
        principal_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
    ) -> None:
        self.eligible_principals[principal_id] = {
            "intensity_bucket": intensity_bucket,
            "theme_tags": list(theme_tags),
            "last_active": datetime.now(timezone.utc),
        }

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str) -> None:
        existing = self.eligible_principals.get(principal_id)
        if existing is None:
            self.upsert_eligible_principal(principal_id, intensity_bucket, [])
            return
        existing["last_active"] = datetime.now(timezone.utc)

    def create_inbox_item(self, message_id: str, recipient_id: str, text: str) -> str:
        inbox_item_id = _new_uuid()
        self.inbox_items[inbox_item_id] = InboxItemRecord(
            inbox_item_id=inbox_item_id,
            message_id=message_id,
            recipient_id=recipient_id,
            text=text,
            created_at=datetime.now(timezone.utc).isoformat(),
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
        if ack_key in self.acks:
            item.state = "responded"
            item.ack_status = self.acks[ack_key]
            return "already_recorded"
        self.acks[ack_key] = reaction
        item.state = "responded"
        item.ack_status = reaction
        if reaction in {"thanks", "helpful", "relate"}:
            message = self.messages.get(item.message_id)
            theme_id = message.theme_tags[0] if message and message.theme_tags else None
            if message and theme_id:
                self.record_affinity(message.principal_id, theme_id, 1.0)
        return "recorded"

    def get_helped_count(self, principal_id: str) -> int:
        recipients = set()
        for (message_id, recipient_id), reaction in self.acks.items():
            message = self.messages.get(message_id)
            if message is None or message.principal_id != principal_id:
                continue
            if reaction not in {"thanks", "helpful", "relate"}:
                continue
            recipients.add(recipient_id)
        return len(recipients)

    def record_affinity(self, sender_id: str, theme_id: str, delta: float) -> None:
        if not theme_id:
            return
        sender_scores = self.affinity_scores.setdefault(sender_id, {})
        current = sender_scores.get(theme_id, 0.0)
        sender_scores[theme_id] = min(50.0, current + delta)

    def get_affinity_map(self, sender_id: str) -> Dict[str, float]:
        return dict(self.affinity_scores.get(sender_id, {}))

    def get_eligible_candidates(
        self,
        sender_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
        limit: int = MATCH_SAMPLE_LIMIT,
    ) -> List[Candidate]:
        if self.candidate_pool:
            return list(self.candidate_pool)[:limit]

        cutoff = datetime.now(timezone.utc) - timedelta(hours=ELIGIBLE_RECENCY_HOURS)
        candidates: List[Candidate] = []
        for principal_id, data in self.eligible_principals.items():
            if principal_id == sender_id:
                continue
            if data["intensity_bucket"] != intensity_bucket:
                continue
            if data["last_active"] < cutoff:
                continue
            if theme_tags and not set(theme_tags).intersection(set(data["theme_tags"])):
                continue
            candidates.append(
                Candidate(
                    candidate_id=principal_id,
                    intensity=data["intensity_bucket"],
                    themes=list(data["theme_tags"]),
                )
            )
            if len(candidates) >= limit:
                break
        return candidates

    def get_matching_health(self, principal_id: str, window_days: int = 7) -> MatchingHealth:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        sender_message_ids = {
            message_id
            for message_id, record in self.messages.items()
            if record.principal_id == principal_id
        }
        delivered_items = []
        for item in self.inbox_items.values():
            if item.message_id not in sender_message_ids:
                continue
            created_at = _parse_iso(item.created_at)
            if created_at is None or created_at < cutoff:
                continue
            delivered_items.append(item)
        delivered_count = len(delivered_items)
        positive_ack_count = 0
        for item in delivered_items:
            reaction = self.acks.get((item.message_id, item.recipient_id))
            if reaction in {"thanks", "helpful", "relate"}:
                positive_ack_count += 1
        ratio = _safe_ratio(positive_ack_count, delivered_count)
        return MatchingHealth(
            delivered_count=delivered_count,
            positive_ack_count=positive_ack_count,
            ratio=ratio,
        )


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

    def record_mood_event(self, record: MoodEventRecord) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mood_events
                (device_id, valence, intensity, expressed_emotion, risk_level, theme_tag, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record.principal_id,
                    record.valence,
                    record.intensity,
                    record.expressed_emotion,
                    record.risk_level,
                    record.theme_tag,
                    record.created_at,
                ),
            )

    def get_reflection_summary(self, principal_id: str, window_days: int) -> ReflectionSummary:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT created_at, valence, intensity, expressed_emotion, risk_level, theme_tag
                FROM mood_events
                WHERE device_id = %s AND created_at >= %s
                ORDER BY created_at ASC
                """,
                (principal_id, cutoff),
            )
            rows = cur.fetchall()
        records = [
            MoodEventRecord(
                principal_id=principal_id,
                created_at=row[0],
                valence=row[1],
                intensity=row[2],
                expressed_emotion=row[3],
                risk_level=row[4],
                theme_tag=row[5],
            )
            for row in rows
        ]
        return _summarize_mood_events(records, window_days)

    def save_message(self, record: MessageRecord) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                (
                  valence,
                  intensity,
                  emotion,
                  theme_tags,
                  risk_level,
                  sanitized_text,
                  reid_risk,
                  status,
                  origin_device_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    record.valence,
                    record.intensity,
                    record.emotion,
                    record.theme_tags,
                    record.risk_level,
                    record.sanitized_text,
                    record.reid_risk,
                    "queued",
                    record.principal_id,
                ),
            )
            return str(cur.fetchone()[0])

    def upsert_eligible_principal(
        self,
        principal_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
    ) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO eligible_principals
                (principal_id, intensity_bucket, theme_tags, last_active_bucket, updated_at)
                VALUES (%s, %s, %s, date_trunc('hour', now()), now())
                ON CONFLICT (principal_id)
                DO UPDATE SET
                  intensity_bucket = EXCLUDED.intensity_bucket,
                  theme_tags = EXCLUDED.theme_tags,
                  last_active_bucket = EXCLUDED.last_active_bucket,
                  updated_at = now()
                """,
                (principal_id, intensity_bucket, theme_tags),
            )

    def touch_eligible_principal(self, principal_id: str, intensity_bucket: str) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO eligible_principals
                (principal_id, intensity_bucket, theme_tags, last_active_bucket, updated_at)
                VALUES (%s, %s, %s, date_trunc('hour', now()), now())
                ON CONFLICT (principal_id)
                DO UPDATE SET
                  last_active_bucket = EXCLUDED.last_active_bucket,
                  updated_at = now()
                """,
                (principal_id, intensity_bucket, []),
            )

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
                DO NOTHING
                RETURNING id
                """,
                (message_id, recipient_id, reaction),
            )
            inserted = cur.fetchone()
        if inserted:
            if reaction in {"thanks", "helpful", "relate"}:
                with self._conn() as conn, conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT origin_device_id, theme_tags
                        FROM messages
                        WHERE id = %s
                        """,
                        (message_id,),
                    )
                    row = cur.fetchone()
                if row and row[0] and row[1]:
                    theme_id = row[1][0] if row[1] else None
                    if theme_id:
                        self.record_affinity(row[0], theme_id, 1.0)
            return "recorded"
        return "already_recorded"

    def get_helped_count(self, principal_id: str) -> int:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT a.recipient_device_id)
                FROM acknowledgements a
                JOIN messages m ON m.id = a.message_id
                WHERE m.origin_device_id = %s
                  AND a.reaction IN ('thanks', 'helpful', 'relate')
                """,
                (principal_id,),
            )
            row = cur.fetchone()
        return int(row[0] or 0)

    def record_affinity(self, sender_id: str, theme_id: str, delta: float) -> None:
        if not theme_id:
            return
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO affinity_scores (sender_device_id, theme_id, score, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (sender_device_id, theme_id)
                DO UPDATE SET
                  score = LEAST(50, affinity_scores.score + EXCLUDED.score),
                  updated_at = now()
                """,
                (sender_id, theme_id, delta),
            )

    def get_affinity_map(self, sender_id: str) -> Dict[str, float]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT theme_id, score
                FROM affinity_scores
                WHERE sender_device_id = %s
                """,
                (sender_id,),
            )
            rows = cur.fetchall()
        return {row[0]: float(row[1]) for row in rows}

    def get_eligible_candidates(
        self,
        sender_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
        limit: int = MATCH_SAMPLE_LIMIT,
    ) -> List[Candidate]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ELIGIBLE_RECENCY_HOURS)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT principal_id, intensity_bucket, theme_tags
                FROM eligible_principals
                WHERE principal_id != %s
                  AND intensity_bucket = %s
                  AND last_active_bucket >= %s
                  AND (%s = '{}' OR theme_tags && %s)
                ORDER BY random()
                LIMIT %s
                """,
                (sender_id, intensity_bucket, cutoff, theme_tags, theme_tags, limit),
            )
            rows = cur.fetchall()
        return [
            Candidate(candidate_id=row[0], intensity=row[1], themes=row[2] or [])
            for row in rows
        ]

    def get_matching_health(self, principal_id: str, window_days: int = 7) -> MatchingHealth:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM inbox_items i
                JOIN messages m ON m.id = i.message_id
                WHERE m.origin_device_id = %s
                  AND i.received_at >= %s
                """,
                (principal_id, cutoff),
            )
            delivered_count = int(cur.fetchone()[0] or 0)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM acknowledgements a
                JOIN messages m ON m.id = a.message_id
                WHERE m.origin_device_id = %s
                  AND a.created_at >= %s
                  AND a.reaction IN ('thanks', 'helpful', 'relate')
                """,
                (principal_id, cutoff),
            )
            positive_ack_count = int(cur.fetchone()[0] or 0)
        ratio = _safe_ratio(positive_ack_count, delivered_count)
        return MatchingHealth(
            delivered_count=delivered_count,
            positive_ack_count=positive_ack_count,
            ratio=ratio,
        )

    def get_similar_count(
        self,
        principal_id: str,
        theme_tag: str,
        valence: str,
        window_days: int,
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(DISTINCT device_id)
                FROM mood_events
                WHERE theme_tag = %s
                  AND valence = %s
                  AND risk_level != 2
                  AND device_id != %s
                  AND created_at >= %s
                """,
                (theme_tag, valence, principal_id, cutoff),
            )
            row = cur.fetchone()
        return int(row[0] or 0)


_default_repo = InMemoryRepository()


def get_repository() -> Repository:
    dsn = os.getenv("POSTGRES_DSN")
    if dsn:
        return PostgresRepository(dsn)
    return _default_repo


def _new_uuid() -> str:
    import uuid

    return str(uuid.uuid4())


def _filter_mood_events(
    records: List[MoodEventRecord],
    principal_id: str,
    window_days: int,
) -> List[MoodEventRecord]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    return [
        record
        for record in records
        if record.principal_id == principal_id and record.created_at >= cutoff
    ]


def _summarize_mood_events(
    records: List[MoodEventRecord],
    window_days: int,
) -> ReflectionSummary:
    distribution: Dict[str, int] = {}
    for record in records:
        if record.expressed_emotion:
            distribution[record.expressed_emotion] = distribution.get(
                record.expressed_emotion,
                0,
            ) + 1

    day_valences: Dict[str, str] = {}
    for record in records:
        day_key = record.created_at.date().isoformat()
        day_valences[day_key] = record.valence

    ordered_days = sorted(day_valences.keys())
    volatility = 0
    last_valence = None
    for day in ordered_days:
        current = day_valences[day]
        if last_valence is not None and current != last_valence:
            volatility += 1
        last_valence = current

    valence_score = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    scores = [valence_score.get(record.valence, 0.0) for record in records]
    trend = "stable"
    if scores:
        mid = max(1, len(scores) // 2)
        first_avg = sum(scores[:mid]) / len(scores[:mid])
        last_avg = sum(scores[mid:]) / len(scores[mid:]) if scores[mid:] else first_avg
        delta = last_avg - first_avg
        if delta > 0.2:
            trend = "up"
        elif delta < -0.2:
            trend = "down"

    return ReflectionSummary(
        window_days=window_days,
        total_entries=len(records),
        distribution=distribution,
        trend=trend,
        volatility_days=volatility,
    )


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
