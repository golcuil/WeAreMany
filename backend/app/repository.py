from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from typing import Dict, List, Optional, Protocol

import os

from .bridge import SYSTEM_SENDER_ID
from .finite_content_store import select_finite_content_id
from .inbox_origin import InboxOrigin
from .matching import Candidate, MatchingTuning, default_matching_tuning
from .config import (
    AFFINITY_DECAY_PER_DAY,
    AFFINITY_SCORE_MAX,
    CRISIS_WINDOW_HOURS,
    ELIGIBLE_RECENCY_HOURS,
    MATCH_SAMPLE_LIMIT,
    SECURITY_EVENT_HMAC_KEY,
    SECOND_TOUCH_COOLDOWN_DAYS,
    SECOND_TOUCH_DISABLE_DAYS,
    SECOND_TOUCH_MIN_AFFINITY,
    SECOND_TOUCH_MIN_POSITIVE,
    SECOND_TOUCH_MIN_SPAN_DAYS,
    SECOND_TOUCH_MONTHLY_CAP,
)
from .hold_reasons import HoldReason

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
    identity_leak: bool = False


@dataclass
class InboxItemRecord:
    inbox_item_id: str
    message_id: str
    recipient_id: str
    text: str
    created_at: str
    state: str
    ack_status: Optional[str]
    origin: str


@dataclass
class InboxListItem:
    item_type: str
    created_at: str
    text: str
    ack_status: Optional[str]
    inbox_item_id: Optional[str] = None
    offer_id: Optional[str] = None
    offer_state: Optional[str] = None


@dataclass
class SecondTouchOfferRecord:
    offer_id: str
    offer_to_id: str
    counterpart_id: str
    state: str
    created_at: datetime
    used_at: Optional[datetime]


@dataclass
class SecurityEventRecord:
    actor_hash: str
    event_type: str
    meta: Dict[str, object]
    created_at: datetime


@dataclass
class DailyAckAggregate:
    utc_day: str
    theme_id: str
    delivered_count: int
    positive_ack_count: int


@dataclass
class SecondTouchDailyAggregate:
    utc_day: str
    counter_key: str
    count: int


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

    def list_inbox_items_with_offers(self, recipient_id: str) -> List[InboxListItem]:
        ...

    def create_second_touch_offer(self, offer_to_id: str, counterpart_id: str) -> str:
        ...

    def get_second_touch_offer(self, offer_id: str) -> Optional[SecondTouchOfferRecord]:
        ...

    def mark_second_touch_offer_used(self, offer_id: str) -> None:
        ...

    def list_second_touch_offers(self, offer_to_id: str) -> List[SecondTouchOfferRecord]:
        ...

    def get_second_touch_hold_reason(
        self,
        offer_to_id: str,
        counterpart_id: str,
        now: datetime,
    ) -> Optional[str]:
        ...

    def update_second_touch_pair_positive(
        self, sender_id: str, recipient_id: str, now: datetime
    ) -> None:
        ...

    def block_second_touch_pair(
        self,
        sender_id: str,
        recipient_id: str,
        until: Optional[datetime],
        permanent: bool,
    ) -> None:
        ...

    def get_helped_count(self, principal_id: str) -> int:
        ...

    def record_affinity(
        self,
        sender_id: str,
        theme_id: str,
        delta: float,
        now: Optional[datetime] = None,
    ) -> None:
        ...

    def get_affinity_map(
        self,
        sender_id: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, float]:
        ...

    def record_crisis_action(
        self,
        principal_id: str,
        action: str,
        now: Optional[datetime] = None,
    ) -> None:
        ...

    def is_in_crisis_window(
        self,
        principal_id: str,
        window_hours: int,
        now: Optional[datetime] = None,
    ) -> bool:
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

    def record_security_event(self, record: SecurityEventRecord) -> None:
        ...

    def prune_security_events(self, now: datetime, retention_days: Optional[int] = None) -> int:
        ...

    def list_daily_ack_aggregates(
        self,
        days: int,
        theme_id: Optional[str] = None,
    ) -> List[DailyAckAggregate]:
        ...

    def increment_second_touch_counter(self, day_key: str, counter_key: str, amount: int = 1) -> None:
        ...

    def get_second_touch_counters(self, window_days: int) -> Dict[str, int]:
        ...

    def cleanup_second_touch_daily_aggregates(
        self,
        retention_days: int,
        now_utc: datetime,
    ) -> int:
        ...

    def recompute_second_touch_daily_aggregates(
        self,
        start_day_utc: datetime.date,
        end_day_utc: datetime.date,
    ) -> Dict[str, object]:
        ...

    def get_matching_tuning(self) -> MatchingTuning:
        ...

    def update_matching_tuning(self, tuning: MatchingTuning, now: datetime) -> None:
        ...

    def get_global_matching_health(self, window_days: int = 7) -> MatchingHealth:
        ...

    def get_or_create_finite_content(
        self,
        principal_id: str,
        day_key: str,
        valence_bucket: str,
        intensity_bucket: str,
        theme_id: Optional[str],
    ) -> str:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self.messages = {}
        self.inbox_items = {}
        self.acks = {}
        self.eligible_principals = {}
        self.candidate_pool: List[Candidate] = []
        self.mood_events: List[MoodEventRecord] = []
        self.affinity_scores: Dict[str, Dict[str, tuple[float, datetime]]] = {}
        self.crisis_state: Dict[str, Dict[str, datetime]] = {}
        self.security_events: List[SecurityEventRecord] = []
        self.matching_tuning = default_matching_tuning()
        self.finite_content_selections: Dict[str, str] = {}
        self.daily_ack_aggregates: Dict[tuple[str, str], DailyAckAggregate] = {}
        self.second_touch_pairs: Dict[tuple[str, str], Dict[str, object]] = {}
        self.second_touch_offers: Dict[str, SecondTouchOfferRecord] = {}
        self.second_touch_counters: Dict[tuple[str, str], int] = {}

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
        message = self.messages.get(message_id)
        origin = (
            InboxOrigin.SYSTEM.value
            if message and message.principal_id == SYSTEM_SENDER_ID
            else InboxOrigin.PEER.value
        )
        theme_id = _normalize_theme_id(message.theme_tags[0]) if message and message.theme_tags else "unknown"
        self.inbox_items[inbox_item_id] = InboxItemRecord(
            inbox_item_id=inbox_item_id,
            message_id=message_id,
            recipient_id=recipient_id,
            text=text,
            created_at=datetime.now(timezone.utc).isoformat(),
            state="unread",
            ack_status=None,
            origin=origin,
        )
        if message and message.identity_leak and message.principal_id != SYSTEM_SENDER_ID:
            self.block_second_touch_pair(
                message.principal_id, recipient_id, until=None, permanent=True
            )
        self._increment_daily_ack_aggregate(
            _utc_day_key(),
            theme_id,
            delivered_delta=1,
            positive_delta=0,
        )
        return inbox_item_id

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        items = [item for item in self.inbox_items.values() if item.recipient_id == recipient_id]
        for item in items:
            ack_key = (item.message_id, recipient_id)
            if ack_key in self.acks:
                item.ack_status = self.acks[ack_key]
                item.state = "responded"
            if not item.origin:
                message = self.messages.get(item.message_id)
                item.origin = (
                    InboxOrigin.SYSTEM.value
                    if message and message.principal_id == SYSTEM_SENDER_ID
                    else InboxOrigin.PEER.value
                )
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
        message = self.messages.get(item.message_id)
        if reaction in {"thanks", "helpful", "relate"}:
            theme_id = message.theme_tags[0] if message and message.theme_tags else None
            if message and theme_id:
                self.record_affinity(message.principal_id, theme_id, 1.0)
            if message:
                self._increment_daily_ack_aggregate(
                    _utc_day_key(),
                    _normalize_theme_id(theme_id),
                    delivered_delta=0,
                    positive_delta=1,
                )
                self.update_second_touch_pair_positive(
                    message.principal_id, recipient_id, datetime.now(timezone.utc)
                )
        else:
            if message:
                disable_until = datetime.now(timezone.utc) + timedelta(
                    days=SECOND_TOUCH_DISABLE_DAYS
                )
                self.block_second_touch_pair(
                    message.principal_id, recipient_id, disable_until, permanent=False
                )
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

    def record_affinity(
        self,
        sender_id: str,
        theme_id: str,
        delta: float,
        now: Optional[datetime] = None,
    ) -> None:
        if not theme_id:
            return
        actor_id = _hash_affinity_actor(sender_id)
        sender_scores = self.affinity_scores.setdefault(actor_id, {})
        timestamp = now or datetime.now(timezone.utc)
        current_score, updated_at = sender_scores.get(theme_id, (0.0, timestamp))
        decayed = _apply_affinity_decay(current_score, updated_at, timestamp)
        next_score = min(AFFINITY_SCORE_MAX, decayed + delta)
        sender_scores[theme_id] = (next_score, timestamp)

    def get_affinity_map(
        self,
        sender_id: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, float]:
        actor_id = _hash_affinity_actor(sender_id)
        timestamp = now or datetime.now(timezone.utc)
        scores = self.affinity_scores.get(actor_id, {})
        result: Dict[str, float] = {}
        for theme_id, (score, updated_at) in scores.items():
            decayed = _apply_affinity_decay(score, updated_at, timestamp)
            if decayed > 0:
                result[theme_id] = decayed
        return result

    def record_crisis_action(
        self,
        principal_id: str,
        action: str,
        now: Optional[datetime] = None,
    ) -> None:
        timestamp = now or datetime.now(timezone.utc)
        self.crisis_state[principal_id] = {"action": action, "at": timestamp}

    def is_in_crisis_window(
        self,
        principal_id: str,
        window_hours: int,
        now: Optional[datetime] = None,
    ) -> bool:
        record = self.crisis_state.get(principal_id)
        if record is None:
            return False
        now_value = now or datetime.now(timezone.utc)
        cutoff = now_value - timedelta(hours=window_hours)
        return record["at"] >= cutoff

    def get_eligible_candidates(
        self,
        sender_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
        limit: int = MATCH_SAMPLE_LIMIT,
    ) -> List[Candidate]:
        day_key = datetime.now(timezone.utc).date().isoformat()
        seed = _candidate_seed(sender_id, day_key)
        if self.candidate_pool:
            filtered = [
                candidate
                for candidate in self.candidate_pool
                if candidate.candidate_id != sender_id
                and not self.is_in_crisis_window(candidate.candidate_id, CRISIS_WINDOW_HOURS)
            ]
            ordered = sorted(filtered, key=lambda c: _candidate_sort_key(c.candidate_id, seed))
            return list(ordered)[:limit]

        cutoff = datetime.now(timezone.utc) - timedelta(hours=ELIGIBLE_RECENCY_HOURS)
        candidates: List[Candidate] = []
        for principal_id, data in self.eligible_principals.items():
            if principal_id == sender_id:
                continue
            if self.is_in_crisis_window(principal_id, CRISIS_WINDOW_HOURS):
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
        ordered = sorted(candidates, key=lambda c: _candidate_sort_key(c.candidate_id, seed))
        return ordered[:limit]

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

    def record_security_event(self, record: SecurityEventRecord) -> None:
        self.security_events.append(record)

    def prune_security_events(self, now: datetime, retention_days: Optional[int] = None) -> int:
        from .config import SECURITY_EVENTS_RETENTION_DAYS

        days = retention_days if retention_days is not None else SECURITY_EVENTS_RETENTION_DAYS
        cutoff = now - timedelta(days=days)
        before = len(self.security_events)
        self.security_events = [
            record for record in self.security_events if record.created_at >= cutoff
        ]
        return before - len(self.security_events)

    def list_daily_ack_aggregates(
        self,
        days: int,
        theme_id: Optional[str] = None,
    ) -> List[DailyAckAggregate]:
        day_cutoff = datetime.now(timezone.utc).date() - timedelta(days=max(days - 1, 0))
        theme_key = _normalize_theme_id(theme_id) if theme_id is not None else None
        results: List[DailyAckAggregate] = []
        for record in self.daily_ack_aggregates.values():
            record_day = datetime.fromisoformat(record.utc_day).date()
            if record_day < day_cutoff:
                continue
            if theme_key is not None and record.theme_id != theme_key:
                continue
            results.append(record)
        results.sort(key=lambda item: item.utc_day, reverse=True)
        return results

    def increment_second_touch_counter(
        self,
        day_key: str,
        counter_key: str,
        amount: int = 1,
    ) -> None:
        key = (day_key, counter_key)
        self.second_touch_counters[key] = self.second_touch_counters.get(key, 0) + amount

    def get_second_touch_counters(self, window_days: int) -> Dict[str, int]:
        day_cutoff = datetime.now(timezone.utc).date() - timedelta(days=max(window_days - 1, 0))
        totals: Dict[str, int] = {}
        for (day_key, counter_key), count in self.second_touch_counters.items():
            record_day = datetime.fromisoformat(day_key).date()
            if record_day < day_cutoff:
                continue
            totals[counter_key] = totals.get(counter_key, 0) + count
        return totals

    def cleanup_second_touch_daily_aggregates(
        self,
        retention_days: int,
        now_utc: datetime,
    ) -> int:
        cutoff = now_utc.date() - timedelta(days=retention_days)
        before = len(self.second_touch_counters)
        self.second_touch_counters = {
            (day_key, counter_key): count
            for (day_key, counter_key), count in self.second_touch_counters.items()
            if datetime.fromisoformat(day_key).date() >= cutoff
        }
        return before - len(self.second_touch_counters)

    def recompute_second_touch_daily_aggregates(
        self,
        start_day_utc: datetime.date,
        end_day_utc: datetime.date,
    ) -> Dict[str, object]:
        recompute_keys = {"offers_generated", "sends_queued"}
        kept: Dict[tuple[str, str], int] = {}
        for (day_key, counter_key), count in self.second_touch_counters.items():
            record_day = datetime.fromisoformat(day_key).date()
            if counter_key in recompute_keys and start_day_utc <= record_day <= end_day_utc:
                continue
            kept[(day_key, counter_key)] = count
        self.second_touch_counters = kept

        counts: Dict[tuple[str, str], int] = {}
        days_written = set()
        for offer in self.second_touch_offers.values():
            created_day = offer.created_at.date()
            if start_day_utc <= created_day <= end_day_utc:
                key = (created_day.isoformat(), "offers_generated")
                counts[key] = counts.get(key, 0) + 1
                days_written.add(created_day)
            if offer.used_at:
                used_day = offer.used_at.date()
                if start_day_utc <= used_day <= end_day_utc:
                    key = (used_day.isoformat(), "sends_queued")
                    counts[key] = counts.get(key, 0) + 1
                    days_written.add(used_day)

        for key, count in counts.items():
            self.second_touch_counters[key] = count

        return {
            "days_written": len(days_written),
            "recompute_partial": True,
            "reason": "missing_source_events",
        }

    def _increment_daily_ack_aggregate(
        self,
        day_key: str,
        theme_id: str,
        delivered_delta: int,
        positive_delta: int,
    ) -> None:
        key = (day_key, theme_id)
        existing = self.daily_ack_aggregates.get(key)
        if existing is None:
            existing = DailyAckAggregate(
                utc_day=day_key,
                theme_id=theme_id,
                delivered_count=0,
                positive_ack_count=0,
            )
            self.daily_ack_aggregates[key] = existing
        existing.delivered_count += delivered_delta
        existing.positive_ack_count += positive_delta

    def list_inbox_items_with_offers(self, recipient_id: str) -> List[InboxListItem]:
        items = [
            InboxListItem(
                item_type="message",
                inbox_item_id=item.inbox_item_id,
                offer_id=None,
                offer_state=None,
                text=item.text,
                created_at=item.created_at,
                ack_status=item.ack_status,
            )
            for item in self.list_inbox_items(recipient_id)
        ]
        now = datetime.now(timezone.utc)
        if not any(offer.state == "available" for offer in self.list_second_touch_offers(recipient_id)):
            self._maybe_create_second_touch_offer(recipient_id, now)
        for offer in self.list_second_touch_offers(recipient_id):
            if offer.state != "available":
                continue
            created_at = offer.created_at.date().isoformat()
            items.append(
                InboxListItem(
                    item_type="second_touch_offer",
                    inbox_item_id=None,
                    offer_id=offer.offer_id,
                    offer_state=offer.state,
                    text="",
                    created_at=created_at,
                    ack_status=None,
                )
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def create_second_touch_offer(self, offer_to_id: str, counterpart_id: str) -> str:
        offer_id = _new_uuid()
        record = SecondTouchOfferRecord(
            offer_id=offer_id,
            offer_to_id=offer_to_id,
            counterpart_id=counterpart_id,
            state="available",
            created_at=datetime.now(timezone.utc),
            used_at=None,
        )
        self.second_touch_offers[offer_id] = record
        return offer_id

    def get_second_touch_offer(self, offer_id: str) -> Optional[SecondTouchOfferRecord]:
        return self.second_touch_offers.get(offer_id)

    def mark_second_touch_offer_used(self, offer_id: str) -> None:
        record = self.second_touch_offers.get(offer_id)
        if record is None:
            return
        record.state = "used"
        record.used_at = datetime.now(timezone.utc)

    def list_second_touch_offers(self, offer_to_id: str) -> List[SecondTouchOfferRecord]:
        return [
            offer
            for offer in self.second_touch_offers.values()
            if offer.offer_to_id == offer_to_id
        ]

    def get_second_touch_hold_reason(
        self,
        offer_to_id: str,
        counterpart_id: str,
        now: datetime,
    ) -> Optional[str]:
        a_id, b_id = _pair_key(offer_to_id, counterpart_id)
        record = self.second_touch_pairs.get((a_id, b_id))
        if record:
            if record.get("disabled_permanent") or record.get("identity_leak_blocked"):
                return HoldReason.IDENTITY_LEAK.value
            disabled_until = record.get("disabled_until")
            if disabled_until and disabled_until > now:
                return HoldReason.COOLDOWN_ACTIVE.value
        offers_last_month = [
            offer
            for offer in self.list_second_touch_offers(offer_to_id)
            if (now - offer.created_at).days < 30
        ]
        if len(offers_last_month) >= SECOND_TOUCH_MONTHLY_CAP:
            return HoldReason.RATE_LIMITED.value
        recent_pair_sends = [
            offer
            for offer in self.second_touch_offers.values()
            if offer.offer_to_id == offer_to_id
            and offer.counterpart_id == counterpart_id
            and offer.used_at
            and (now - offer.used_at).days < SECOND_TOUCH_COOLDOWN_DAYS
        ]
        if recent_pair_sends:
            return HoldReason.COOLDOWN_ACTIVE.value
        return None

    def update_second_touch_pair_positive(
        self, sender_id: str, recipient_id: str, now: datetime
    ) -> None:
        a_id, b_id = _pair_key(sender_id, recipient_id)
        record = self.second_touch_pairs.get((a_id, b_id))
        if record is None:
            record = {
                "a_id": a_id,
                "b_id": b_id,
                "positive_count": 0,
                "first_positive_at": now,
                "last_positive_at": now,
                "last_offer_at": None,
                "disabled_until": None,
                "disabled_permanent": False,
                "identity_leak_blocked": False,
            }
            self.second_touch_pairs[(a_id, b_id)] = record
        record["positive_count"] = int(record["positive_count"]) + 1
        record["last_positive_at"] = now
        if record.get("first_positive_at") is None:
            record["first_positive_at"] = now

    def block_second_touch_pair(
        self,
        sender_id: str,
        recipient_id: str,
        until: Optional[datetime],
        permanent: bool,
    ) -> None:
        day_key = _utc_day_key()
        if permanent:
            self.increment_second_touch_counter(day_key, "disables_identity_leak")
        elif until:
            self.increment_second_touch_counter(day_key, "disables_negative_ack")
        a_id, b_id = _pair_key(sender_id, recipient_id)
        record = self.second_touch_pairs.get((a_id, b_id))
        if record is None:
            record = {
                "a_id": a_id,
                "b_id": b_id,
                "positive_count": 0,
                "first_positive_at": None,
                "last_positive_at": None,
                "last_offer_at": None,
                "disabled_until": None,
                "disabled_permanent": False,
                "identity_leak_blocked": False,
            }
            self.second_touch_pairs[(a_id, b_id)] = record
        if permanent:
            record["disabled_permanent"] = True
            record["identity_leak_blocked"] = True
        if until:
            current = record.get("disabled_until")
            if current is None or until > current:
                record["disabled_until"] = until

    def _maybe_create_second_touch_offer(self, recipient_id: str, now: datetime) -> None:
        day_key = _utc_day_key(now)
        for (a_id, b_id), record in self.second_touch_pairs.items():
            if recipient_id not in (a_id, b_id):
                continue
            counterpart_id = b_id if recipient_id == a_id else a_id
            if record.get("disabled_permanent"):
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("disabled_permanent"),
                )
                continue
            disabled_until = record.get("disabled_until")
            if disabled_until and disabled_until > now:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("disabled_until_active"),
                )
                continue
            positive_count = int(record.get("positive_count") or 0)
            if positive_count < SECOND_TOUCH_MIN_POSITIVE or positive_count < SECOND_TOUCH_MIN_AFFINITY:
                continue
            first_positive_at = record.get("first_positive_at")
            last_positive_at = record.get("last_positive_at")
            if not first_positive_at or not last_positive_at:
                continue
            if (last_positive_at - first_positive_at).days < SECOND_TOUCH_MIN_SPAN_DAYS:
                continue
            if (now - last_positive_at).days < SECOND_TOUCH_COOLDOWN_DAYS:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("cooldown_active"),
                )
                continue
            last_offer_at = record.get("last_offer_at")
            if last_offer_at and (now - last_offer_at).days < SECOND_TOUCH_COOLDOWN_DAYS:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("cooldown_active"),
                )
                continue
            if self.is_in_crisis_window(recipient_id, CRISIS_WINDOW_HOURS, now):
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("crisis_blocked"),
                )
                continue
            if self.is_in_crisis_window(counterpart_id, CRISIS_WINDOW_HOURS, now):
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("crisis_blocked"),
                )
                continue
            hold_reason = self.get_second_touch_hold_reason(
                recipient_id,
                counterpart_id,
                now,
            )
            if hold_reason:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key(_suppression_reason_from_hold(hold_reason)),
                )
                continue
            offers_last_month = [
                offer
                for offer in self.list_second_touch_offers(recipient_id)
                if (now - offer.created_at).days < 30
            ]
            if len(offers_last_month) >= SECOND_TOUCH_MONTHLY_CAP:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("rate_limited"),
                )
                continue
            latest_a = _latest_mood_event(self.mood_events, recipient_id)
            latest_b = _latest_mood_event(self.mood_events, counterpart_id)
            if not _is_emotionally_compatible(latest_a, latest_b, now):
                continue
            self.create_second_touch_offer(recipient_id, counterpart_id)
            self.increment_second_touch_counter(day_key, "offers_generated")
            record["last_offer_at"] = now
            return

    def get_matching_tuning(self) -> MatchingTuning:
        return self.matching_tuning

    def update_matching_tuning(self, tuning: MatchingTuning, now: datetime) -> None:
        self.matching_tuning = tuning

    def get_global_matching_health(self, window_days: int = 7) -> MatchingHealth:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        delivered = []
        for item in self.inbox_items.values():
            created_at = _parse_iso(item.created_at)
            if created_at is None or created_at < cutoff:
                continue
            message = self.messages.get(item.message_id)
            if message is None:
                continue
            if message.principal_id == SYSTEM_SENDER_ID:
                continue
            delivered.append(item)
        delivered_count = len(delivered)
        positive_ack_count = 0
        for item in delivered:
            reaction = self.acks.get((item.message_id, item.recipient_id))
            if reaction in {"thanks", "helpful", "relate"}:
                positive_ack_count += 1
        ratio = _safe_ratio(positive_ack_count, delivered_count)
        return MatchingHealth(
            delivered_count=delivered_count,
            positive_ack_count=positive_ack_count,
            ratio=ratio,
        )

    def get_or_create_finite_content(
        self,
        principal_id: str,
        day_key: str,
        valence_bucket: str,
        intensity_bucket: str,
        theme_id: Optional[str],
    ) -> str:
        key = f"{principal_id}:{day_key}:{valence_bucket}:{intensity_bucket}:{theme_id or 'none'}"
        existing = self.finite_content_selections.get(key)
        if existing:
            return existing
        content_id = select_finite_content_id(
            principal_id,
            day_key,
            valence_bucket,
            intensity_bucket,
            theme_id,
        )
        self.finite_content_selections[key] = content_id
        return content_id


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
                  identity_leak,
                  status,
                  origin_device_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    record.identity_leak,
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
                SELECT theme_tags, origin_device_id, identity_leak
                FROM messages
                WHERE id = %s
                """,
                (message_id,),
            )
            row = cur.fetchone()
            theme_id = _normalize_theme_id(row[0][0]) if row and row[0] else "unknown"
            origin_device_id = row[1] if row else None
            identity_leak = bool(row[2]) if row else False
            cur.execute(
                """
                INSERT INTO inbox_items
                (message_id, recipient_device_id, state)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (message_id, recipient_id, "unread"),
            )
            inbox_item_id = str(cur.fetchone()[0])
            self._increment_daily_ack_aggregate(
                cur,
                _utc_day_key(),
                theme_id,
                delivered_delta=1,
                positive_delta=0,
            )
            if identity_leak and origin_device_id and origin_device_id != SYSTEM_SENDER_ID:
                self.block_second_touch_pair(
                    origin_device_id, recipient_id, until=None, permanent=True
                )
            return inbox_item_id

    def list_inbox_items(self, recipient_id: str) -> List[InboxItemRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT i.id, i.message_id, i.recipient_device_id, i.state, i.received_at,
                       m.sanitized_text,
                       a.reaction,
                       m.origin_device_id
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
            origin = (
                InboxOrigin.SYSTEM.value
                if row[7] == SYSTEM_SENDER_ID
                else InboxOrigin.PEER.value
            )
            items.append(
                InboxItemRecord(
                    inbox_item_id=str(row[0]),
                    message_id=str(row[1]),
                    recipient_id=row[2],
                    state=row[3],
                    created_at=row[4].isoformat(),
                    text=row[5] or "",
                    ack_status=row[6],
                    origin=origin,
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
                        with self._conn() as conn, conn.cursor() as cur:
                            self._increment_daily_ack_aggregate(
                                cur,
                                _utc_day_key(),
                                _normalize_theme_id(theme_id),
                                delivered_delta=0,
                                positive_delta=1,
                            )
                        self.update_second_touch_pair_positive(
                            row[0], recipient_id, datetime.now(timezone.utc)
                        )
            return "recorded"
        if reaction not in {"thanks", "helpful", "relate"}:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT origin_device_id
                    FROM messages
                    WHERE id = %s
                    """,
                    (message_id,),
                )
                row = cur.fetchone()
            if row and row[0]:
                disable_until = datetime.now(timezone.utc) + timedelta(
                    days=SECOND_TOUCH_DISABLE_DAYS
                )
                self.block_second_touch_pair(
                    row[0], recipient_id, disable_until, permanent=False
                )
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

    def record_affinity(
        self,
        sender_id: str,
        theme_id: str,
        delta: float,
        now: Optional[datetime] = None,
    ) -> None:
        if not theme_id:
            return
        actor_id = _hash_affinity_actor(sender_id)
        timestamp = now or datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT score, updated_at
                FROM affinity_scores
                WHERE sender_device_id = %s AND theme_id = %s
                """,
                (actor_id, theme_id),
            )
            row = cur.fetchone()
            current = float(row[0]) if row else 0.0
            updated_at = row[1] if row else timestamp
            decayed = _apply_affinity_decay(current, updated_at, timestamp)
            next_score = min(AFFINITY_SCORE_MAX, decayed + delta)
            cur.execute(
                """
                INSERT INTO affinity_scores (sender_device_id, theme_id, score, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (sender_device_id, theme_id)
                DO UPDATE SET
                  score = EXCLUDED.score,
                  updated_at = EXCLUDED.updated_at
                """,
                (actor_id, theme_id, next_score, timestamp),
            )

    def get_affinity_map(
        self,
        sender_id: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, float]:
        actor_id = _hash_affinity_actor(sender_id)
        timestamp = now or datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT theme_id, score, updated_at
                FROM affinity_scores
                WHERE sender_device_id = %s
                """,
                (actor_id,),
            )
            rows = cur.fetchall()
        result: Dict[str, float] = {}
        for theme_id, score, updated_at in rows:
            decayed = _apply_affinity_decay(float(score), updated_at, timestamp)
            if decayed > 0:
                result[theme_id] = decayed
        return result

    def record_crisis_action(
        self,
        principal_id: str,
        action: str,
        now: Optional[datetime] = None,
    ) -> None:
        timestamp = now or datetime.now(timezone.utc)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO principal_crisis_state
                (principal_id, last_action, last_action_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (principal_id)
                DO UPDATE SET
                  last_action = EXCLUDED.last_action,
                  last_action_at = EXCLUDED.last_action_at
                """,
                (principal_id, action, timestamp),
            )

    def is_in_crisis_window(
        self,
        principal_id: str,
        window_hours: int,
        now: Optional[datetime] = None,
    ) -> bool:
        now_value = now or datetime.now(timezone.utc)
        cutoff = now_value - timedelta(hours=window_hours)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_action_at
                FROM principal_crisis_state
                WHERE principal_id = %s
                """,
                (principal_id,),
            )
            row = cur.fetchone()
        if row is None or row[0] is None:
            return False
        return row[0] >= cutoff

    def get_eligible_candidates(
        self,
        sender_id: str,
        intensity_bucket: str,
        theme_tags: List[str],
        limit: int = MATCH_SAMPLE_LIMIT,
    ) -> List[Candidate]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ELIGIBLE_RECENCY_HOURS)
        crisis_cutoff = datetime.now(timezone.utc) - timedelta(hours=CRISIS_WINDOW_HOURS)
        safe_limit = min(max(int(limit), 1), 100)
        day_key = datetime.now(timezone.utc).date().isoformat()
        seed = _candidate_seed(sender_id, day_key)
        with self._conn() as conn, conn.cursor() as cur:
            if theme_tags:
                cur.execute(
                    """
                    SELECT principal_id, intensity_bucket, theme_tags
                    FROM eligible_principals
                    WHERE principal_id != %s
                      AND intensity_bucket = %s
                      AND last_active_bucket >= %s
                      AND NOT EXISTS (
                        SELECT 1
                        FROM principal_crisis_state pcs
                        WHERE pcs.principal_id = eligible_principals.principal_id
                          AND pcs.last_action_at >= %s
                      )
                      AND theme_tags && %s
                    ORDER BY md5(principal_id || %s)
                    LIMIT %s
                    """,
                    (
                        sender_id,
                        intensity_bucket,
                        cutoff,
                        crisis_cutoff,
                        theme_tags,
                        seed,
                        safe_limit,
                    ),
                )
            else:
                cur.execute(
                    """
                    SELECT principal_id, intensity_bucket, theme_tags
                    FROM eligible_principals
                    WHERE principal_id != %s
                      AND intensity_bucket = %s
                      AND last_active_bucket >= %s
                      AND NOT EXISTS (
                        SELECT 1
                        FROM principal_crisis_state pcs
                        WHERE pcs.principal_id = eligible_principals.principal_id
                          AND pcs.last_action_at >= %s
                      )
                    ORDER BY md5(principal_id || %s)
                    LIMIT %s
                    """,
                    (
                        sender_id,
                        intensity_bucket,
                        cutoff,
                        crisis_cutoff,
                        seed,
                        safe_limit,
                    ),
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

    def record_security_event(self, record: SecurityEventRecord) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            meta_payload = record.meta or {}
            from psycopg.types.json import Json

            meta_payload = Json(meta_payload)
            cur.execute(
                """
                INSERT INTO security_events
                (actor_hash, event_type, meta, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (record.actor_hash, record.event_type, meta_payload, record.created_at),
            )

    def prune_security_events(self, now: datetime, retention_days: Optional[int] = None) -> int:
        from .config import SECURITY_EVENTS_RETENTION_DAYS

        days = retention_days if retention_days is not None else SECURITY_EVENTS_RETENTION_DAYS
        cutoff = now - timedelta(days=days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM security_events
                WHERE created_at < %s
                """,
                (cutoff,),
            )
            deleted = cur.rowcount or 0
        return int(deleted)

    def list_daily_ack_aggregates(
        self,
        days: int,
        theme_id: Optional[str] = None,
    ) -> List[DailyAckAggregate]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=max(days - 1, 0))
        with self._conn() as conn, conn.cursor() as cur:
            if theme_id is None:
                cur.execute(
                    """
                    SELECT utc_day, theme_id, delivered_count, positive_ack_count
                    FROM daily_ack_aggregates
                    WHERE utc_day >= %s
                    ORDER BY utc_day DESC, theme_id
                    """,
                    (cutoff,),
                )
            else:
                cur.execute(
                    """
                    SELECT utc_day, theme_id, delivered_count, positive_ack_count
                    FROM daily_ack_aggregates
                    WHERE utc_day >= %s AND theme_id = %s
                    ORDER BY utc_day DESC, theme_id
                    """,
                    (cutoff, _normalize_theme_id(theme_id)),
                )
            rows = cur.fetchall()
        return [
            DailyAckAggregate(
                utc_day=row[0].isoformat(),
                theme_id=row[1],
                delivered_count=int(row[2] or 0),
                positive_ack_count=int(row[3] or 0),
            )
            for row in rows
        ]

    def increment_second_touch_counter(
        self,
        day_key: str,
        counter_key: str,
        amount: int = 1,
    ) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO second_touch_daily_aggregates
                (utc_day, counter_key, count)
                VALUES (%s, %s, %s)
                ON CONFLICT (utc_day, counter_key)
                DO UPDATE SET
                  count = second_touch_daily_aggregates.count + EXCLUDED.count
                """,
                (day_key, counter_key, amount),
            )

    def get_second_touch_counters(self, window_days: int) -> Dict[str, int]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=max(window_days - 1, 0))
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT counter_key, SUM(count)
                FROM second_touch_daily_aggregates
                WHERE utc_day >= %s
                GROUP BY counter_key
                """,
                (cutoff,),
            )
            rows = cur.fetchall()
        return {row[0]: int(row[1] or 0) for row in rows}

    def cleanup_second_touch_daily_aggregates(
        self,
        retention_days: int,
        now_utc: datetime,
    ) -> int:
        cutoff = now_utc.date() - timedelta(days=retention_days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM second_touch_daily_aggregates
                WHERE utc_day < %s
                """,
                (cutoff,),
            )
            deleted = cur.rowcount or 0
        return int(deleted)

    def recompute_second_touch_daily_aggregates(
        self,
        start_day_utc: datetime.date,
        end_day_utc: datetime.date,
    ) -> Dict[str, object]:
        recompute_keys = ["offers_generated", "sends_queued"]
        offer_counts: Dict[datetime.date, int] = {}
        send_counts: Dict[datetime.date, int] = {}
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM second_touch_daily_aggregates
                WHERE utc_day BETWEEN %s AND %s
                  AND counter_key = ANY(%s)
                """,
                (start_day_utc, end_day_utc, recompute_keys),
            )
            cur.execute(
                """
                SELECT created_at::date, COUNT(*)
                FROM second_touch_offers
                WHERE created_at::date BETWEEN %s AND %s
                GROUP BY created_at::date
                """,
                (start_day_utc, end_day_utc),
            )
            for day, count in cur.fetchall():
                offer_counts[day] = int(count or 0)
            cur.execute(
                """
                SELECT used_at::date, COUNT(*)
                FROM second_touch_offers
                WHERE used_at IS NOT NULL
                  AND used_at::date BETWEEN %s AND %s
                GROUP BY used_at::date
                """,
                (start_day_utc, end_day_utc),
            )
            for day, count in cur.fetchall():
                send_counts[day] = int(count or 0)

            inserts = []
            for day, count in offer_counts.items():
                inserts.append((day, "offers_generated", count))
            for day, count in send_counts.items():
                inserts.append((day, "sends_queued", count))
            if inserts:
                cur.executemany(
                    """
                    INSERT INTO second_touch_daily_aggregates
                      (utc_day, counter_key, count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (utc_day, counter_key)
                    DO UPDATE SET count = EXCLUDED.count
                    """,
                    inserts,
                )

        days_written = {day for day in offer_counts} | {day for day in send_counts}
        return {
            "days_written": len(days_written),
            "recompute_partial": True,
            "reason": "missing_source_events",
        }

    def _increment_daily_ack_aggregate(
        self,
        cur,
        day_key: str,
        theme_id: str,
        delivered_delta: int,
        positive_delta: int,
    ) -> None:
        cur.execute(
            """
            INSERT INTO daily_ack_aggregates
              (utc_day, theme_id, delivered_count, positive_ack_count, updated_at)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (utc_day, theme_id)
            DO UPDATE SET
              delivered_count = daily_ack_aggregates.delivered_count + EXCLUDED.delivered_count,
              positive_ack_count = daily_ack_aggregates.positive_ack_count + EXCLUDED.positive_ack_count,
              updated_at = now()
            """,
            (day_key, theme_id, delivered_delta, positive_delta),
        )

    def get_matching_tuning(self) -> MatchingTuning:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT low_intensity_band,
                       high_intensity_band,
                       pool_multiplier_low,
                       pool_multiplier_high,
                       allow_theme_relax_high
                FROM matching_tuning
                WHERE id = 1
                """,
            )
            row = cur.fetchone()
        if row is None:
            return default_matching_tuning()
        return MatchingTuning(
            low_intensity_band=row[0],
            high_intensity_band=row[1],
            pool_multiplier_low=float(row[2]),
            pool_multiplier_high=float(row[3]),
            allow_theme_relax_high=bool(row[4]),
        )

    def update_matching_tuning(self, tuning: MatchingTuning, now: datetime) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO matching_tuning
                (id, low_intensity_band, high_intensity_band, pool_multiplier_low, pool_multiplier_high, allow_theme_relax_high, updated_at)
                VALUES (1, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                  low_intensity_band = EXCLUDED.low_intensity_band,
                  high_intensity_band = EXCLUDED.high_intensity_band,
                  pool_multiplier_low = EXCLUDED.pool_multiplier_low,
                  pool_multiplier_high = EXCLUDED.pool_multiplier_high,
                  allow_theme_relax_high = EXCLUDED.allow_theme_relax_high,
                  updated_at = EXCLUDED.updated_at
                """,
                (
                    tuning.low_intensity_band,
                    tuning.high_intensity_band,
                    tuning.pool_multiplier_low,
                    tuning.pool_multiplier_high,
                    tuning.allow_theme_relax_high,
                    now,
                ),
            )

    def get_global_matching_health(self, window_days: int = 7) -> MatchingHealth:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM inbox_items i
                JOIN messages m ON i.message_id = m.id
                WHERE i.received_at >= %s
                  AND m.origin_device_id != %s
                """,
                (cutoff, SYSTEM_SENDER_ID),
            )
            delivered_count = int(cur.fetchone()[0] or 0)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM acknowledgements a
                JOIN messages m ON a.message_id = m.id
                WHERE a.created_at >= %s
                  AND a.reaction IN ('helpful', 'thanks', 'relate')
                  AND m.origin_device_id != %s
                """,
                (cutoff, SYSTEM_SENDER_ID),
            )
            positive_ack_count = int(cur.fetchone()[0] or 0)
        ratio = _safe_ratio(positive_ack_count, delivered_count)
        return MatchingHealth(
            delivered_count=delivered_count,
            positive_ack_count=positive_ack_count,
            ratio=ratio,
        )

    def get_or_create_finite_content(
        self,
        principal_id: str,
        day_key: str,
        valence_bucket: str,
        intensity_bucket: str,
        theme_id: Optional[str],
    ) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT content_id
                FROM finite_content_selections
                WHERE principal_id = %s
                  AND day_key = %s
                  AND valence_bucket = %s
                  AND intensity_bucket = %s
                  AND theme_id = %s
                """,
                (principal_id, day_key, valence_bucket, intensity_bucket, theme_id),
            )
            row = cur.fetchone()
            if row:
                return row[0]

            content_id = select_finite_content_id(
                principal_id,
                day_key,
                valence_bucket,
                intensity_bucket,
                theme_id,
            )
            cur.execute(
                """
                INSERT INTO finite_content_selections
                (principal_id, day_key, valence_bucket, intensity_bucket, theme_id, content_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
                """,
                (
                    principal_id,
                    day_key,
                    valence_bucket,
                    intensity_bucket,
                    theme_id,
                    content_id,
                ),
            )
        return content_id

    def list_inbox_items_with_offers(self, recipient_id: str) -> List[InboxListItem]:
        items = [
            InboxListItem(
                item_type="message",
                inbox_item_id=item.inbox_item_id,
                offer_id=None,
                offer_state=None,
                text=item.text,
                created_at=item.created_at,
                ack_status=item.ack_status,
            )
            for item in self.list_inbox_items(recipient_id)
        ]
        now = datetime.now(timezone.utc)
        if not any(offer.state == "available" for offer in self.list_second_touch_offers(recipient_id)):
            self._maybe_create_second_touch_offer(recipient_id, now)
        for offer in self.list_second_touch_offers(recipient_id):
            if offer.state != "available":
                continue
            created_at = offer.created_at.date().isoformat()
            items.append(
                InboxListItem(
                    item_type="second_touch_offer",
                    inbox_item_id=None,
                    offer_id=offer.offer_id,
                    offer_state=offer.state,
                    text="",
                    created_at=created_at,
                    ack_status=None,
                )
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def create_second_touch_offer(self, offer_to_id: str, counterpart_id: str) -> str:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO second_touch_offers
                (offer_to_id, counterpart_id, state)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (offer_to_id, counterpart_id, "available"),
            )
            return str(cur.fetchone()[0])

    def get_second_touch_offer(self, offer_id: str) -> Optional[SecondTouchOfferRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, offer_to_id, counterpart_id, state, created_at, used_at
                FROM second_touch_offers
                WHERE id = %s
                """,
                (offer_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return SecondTouchOfferRecord(
            offer_id=str(row[0]),
            offer_to_id=row[1],
            counterpart_id=row[2],
            state=row[3],
            created_at=row[4],
            used_at=row[5],
        )

    def mark_second_touch_offer_used(self, offer_id: str) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE second_touch_offers
                SET state = 'used', used_at = now()
                WHERE id = %s
                """,
                (offer_id,),
            )

    def list_second_touch_offers(self, offer_to_id: str) -> List[SecondTouchOfferRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, offer_to_id, counterpart_id, state, created_at, used_at
                FROM second_touch_offers
                WHERE offer_to_id = %s
                ORDER BY created_at DESC
                """,
                (offer_to_id,),
            )
            rows = cur.fetchall()
        return [
            SecondTouchOfferRecord(
                offer_id=str(row[0]),
                offer_to_id=row[1],
                counterpart_id=row[2],
                state=row[3],
                created_at=row[4],
                used_at=row[5],
            )
            for row in rows
        ]

    def get_second_touch_hold_reason(
        self,
        offer_to_id: str,
        counterpart_id: str,
        now: datetime,
    ) -> Optional[str]:
        a_id, b_id = _pair_key(offer_to_id, counterpart_id)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT disabled_until, disabled_permanent, identity_leak_blocked
                FROM second_touch_pairs
                WHERE sender_id = %s AND recipient_id = %s
                """,
                (a_id, b_id),
            )
            row = cur.fetchone()
        if row:
            disabled_until, disabled_permanent, identity_leak_blocked = row
            if disabled_permanent or identity_leak_blocked:
                return HoldReason.IDENTITY_LEAK.value
            if disabled_until and disabled_until > now:
                return HoldReason.COOLDOWN_ACTIVE.value
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM second_touch_offers
                WHERE offer_to_id = %s AND created_at >= %s
                """,
                (offer_to_id, now - timedelta(days=30)),
            )
            offer_count = int(cur.fetchone()[0] or 0)
        if offer_count >= SECOND_TOUCH_MONTHLY_CAP:
            return HoldReason.RATE_LIMITED.value
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM second_touch_offers
                WHERE offer_to_id = %s AND counterpart_id = %s AND used_at >= %s
                """,
                (offer_to_id, counterpart_id, now - timedelta(days=SECOND_TOUCH_COOLDOWN_DAYS)),
            )
            recent_sends = int(cur.fetchone()[0] or 0)
        if recent_sends > 0:
            return HoldReason.COOLDOWN_ACTIVE.value
        return None

    def update_second_touch_pair_positive(
        self, sender_id: str, recipient_id: str, now: datetime
    ) -> None:
        a_id, b_id = _pair_key(sender_id, recipient_id)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO second_touch_pairs
                (sender_id, recipient_id, positive_count, first_positive_at, last_positive_at)
                VALUES (%s, %s, 1, %s, %s)
                ON CONFLICT (sender_id, recipient_id)
                DO UPDATE SET
                  positive_count = second_touch_pairs.positive_count + 1,
                  last_positive_at = EXCLUDED.last_positive_at,
                  first_positive_at = COALESCE(second_touch_pairs.first_positive_at, EXCLUDED.first_positive_at)
                """,
                (a_id, b_id, now, now),
            )

    def block_second_touch_pair(
        self,
        sender_id: str,
        recipient_id: str,
        until: Optional[datetime],
        permanent: bool,
    ) -> None:
        day_key = _utc_day_key()
        if permanent:
            self.increment_second_touch_counter(day_key, "disables_identity_leak")
        elif until:
            self.increment_second_touch_counter(day_key, "disables_negative_ack")
        a_id, b_id = _pair_key(sender_id, recipient_id)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO second_touch_pairs
                (sender_id, recipient_id, disabled_until, disabled_permanent, identity_leak_blocked)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (sender_id, recipient_id)
                DO UPDATE SET
                  disabled_until = COALESCE(EXCLUDED.disabled_until, second_touch_pairs.disabled_until),
                  disabled_permanent = second_touch_pairs.disabled_permanent OR EXCLUDED.disabled_permanent,
                  identity_leak_blocked = second_touch_pairs.identity_leak_blocked OR EXCLUDED.identity_leak_blocked
                """,
                (a_id, b_id, until, permanent, permanent),
            )

    def _maybe_create_second_touch_offer(self, recipient_id: str, now: datetime) -> None:
        day_key = _utc_day_key(now)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender_id, recipient_id, positive_count, first_positive_at, last_positive_at,
                       last_offer_at, disabled_until, disabled_permanent
                FROM second_touch_pairs
                WHERE sender_id = %s OR recipient_id = %s
                """,
                (recipient_id, recipient_id),
            )
            rows = cur.fetchall()
        for row in rows:
            a_id, b_id = row[0], row[1]
            counterpart_id = b_id if recipient_id == a_id else a_id
            positive_count = int(row[2] or 0)
            first_positive_at = row[3]
            last_positive_at = row[4]
            last_offer_at = row[5]
            disabled_until = row[6]
            disabled_permanent = bool(row[7])
            if disabled_permanent:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("disabled_permanent"),
                )
                continue
            if disabled_until and disabled_until > now:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("disabled_until_active"),
                )
                continue
            if positive_count < SECOND_TOUCH_MIN_POSITIVE or positive_count < SECOND_TOUCH_MIN_AFFINITY:
                continue
            if not first_positive_at or not last_positive_at:
                continue
            if (last_positive_at - first_positive_at).days < SECOND_TOUCH_MIN_SPAN_DAYS:
                continue
            if (now - last_positive_at).days < SECOND_TOUCH_COOLDOWN_DAYS:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("cooldown_active"),
                )
                continue
            if last_offer_at and (now - last_offer_at).days < SECOND_TOUCH_COOLDOWN_DAYS:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("cooldown_active"),
                )
                continue
            if self.is_in_crisis_window(recipient_id, CRISIS_WINDOW_HOURS, now):
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("crisis_blocked"),
                )
                continue
            if self.is_in_crisis_window(counterpart_id, CRISIS_WINDOW_HOURS, now):
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key("crisis_blocked"),
                )
                continue
            hold_reason = self.get_second_touch_hold_reason(recipient_id, counterpart_id, now)
            if hold_reason:
                self.increment_second_touch_counter(
                    day_key,
                    _second_touch_suppressed_key(_suppression_reason_from_hold(hold_reason)),
                )
                continue
            latest_a = self._latest_mood_event_db(recipient_id)
            latest_b = self._latest_mood_event_db(counterpart_id)
            if not _is_emotionally_compatible(latest_a, latest_b, now):
                continue
            self.create_second_touch_offer(recipient_id, counterpart_id)
            self.increment_second_touch_counter(day_key, "offers_generated")
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE second_touch_pairs
                    SET last_offer_at = %s
                    WHERE sender_id = %s AND recipient_id = %s
                    """,
                    (now, a_id, b_id),
                )
            return

    def _latest_mood_event_db(self, principal_id: str) -> Optional[MoodEventRecord]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT created_at, valence, intensity, expressed_emotion, risk_level, theme_tag
                FROM mood_events
                WHERE device_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (principal_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return MoodEventRecord(
            principal_id=principal_id,
            created_at=row[0],
            valence=row[1],
            intensity=row[2],
            expressed_emotion=row[3],
            risk_level=row[4],
            theme_tag=row[5],
        )


def _hash_affinity_actor(principal_id: str) -> str:
    key = SECURITY_EVENT_HMAC_KEY.encode("utf-8")
    message = principal_id.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _apply_affinity_decay(
    score: float,
    updated_at: datetime,
    now: datetime,
) -> float:
    elapsed_days = max(0, (now - updated_at).days)
    if elapsed_days == 0:
        return score
    return score * (AFFINITY_DECAY_PER_DAY ** elapsed_days)


def _candidate_seed(sender_id: str, day_key: str) -> str:
    return f"{sender_id}:{day_key}"


def _candidate_sort_key(candidate_id: str, seed: str) -> str:
    digest = hashlib.sha256(f"{candidate_id}:{seed}".encode("utf-8")).hexdigest()
    return digest


def _utc_day_key(now: Optional[datetime] = None) -> str:
    timestamp = now or datetime.now(timezone.utc)
    return timestamp.date().isoformat()


def _normalize_theme_id(theme_id: Optional[str]) -> str:
    return theme_id or "unknown"


def _second_touch_suppressed_key(reason: str) -> str:
    return f"offers_suppressed_{reason}"


def _second_touch_held_key(reason: str) -> str:
    return f"sends_held_{reason}"


def _suppression_reason_from_hold(hold_reason: str) -> str:
    if hold_reason == HoldReason.RATE_LIMITED.value:
        return "rate_limited"
    if hold_reason == HoldReason.COOLDOWN_ACTIVE.value:
        return "cooldown_active"
    if hold_reason == HoldReason.IDENTITY_LEAK.value:
        return "disabled_permanent"
    return "unknown"


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


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


def _latest_mood_event(
    records: List[MoodEventRecord],
    principal_id: str,
) -> Optional[MoodEventRecord]:
    filtered = [record for record in records if record.principal_id == principal_id]
    if not filtered:
        return None
    filtered.sort(key=lambda record: record.created_at, reverse=True)
    return filtered[0]


def _is_emotionally_compatible(
    a: Optional[MoodEventRecord],
    b: Optional[MoodEventRecord],
    now: datetime,
) -> bool:
    if a is None or b is None:
        return False
    if a.risk_level == 2 or b.risk_level == 2:
        return False
    if a.valence != b.valence:
        return False
    recent_cutoff = now - timedelta(days=14)
    return a.created_at >= recent_cutoff and b.created_at >= recent_cutoff


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
