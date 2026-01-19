import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError


class EventName(str, Enum):
    MOOD_SUBMITTED = "mood_submitted"
    MESSAGE_SUBMITTED = "message_submitted"
    MODERATION_FLAGGED = "moderation_flagged"
    MATCH_DECISION = "match_decision"
    DELIVERY_ATTEMPTED = "delivery_attempted"
    ACK_RECEIVED = "ack_received"
    CRISIS_BLOCKED = "crisis_blocked"


class EventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MoodSubmittedEvent(EventPayload):
    request_id: str
    intensity_bucket: str
    risk_bucket: int
    has_free_text: bool


class MessageSubmittedEvent(EventPayload):
    request_id: str
    intensity_bucket: str
    risk_bucket: int
    identity_leak: bool
    status: str


class ModerationFlaggedEvent(EventPayload):
    request_id: str
    risk_bucket: int
    identity_leak: bool
    leak_type_count: int


class MatchDecisionEvent(EventPayload):
    request_id: str
    risk_bucket: int
    intensity_bucket: str
    decision: str
    reason: str


class DeliveryAttemptedEvent(EventPayload):
    request_id: str
    outcome: str


class AckReceivedEvent(EventPayload):
    request_id: str
    reaction: str


class CrisisBlockedEvent(EventPayload):
    request_id: str
    risk_bucket: int


EVENT_SCHEMAS = {
    EventName.MOOD_SUBMITTED: MoodSubmittedEvent,
    EventName.MESSAGE_SUBMITTED: MessageSubmittedEvent,
    EventName.MODERATION_FLAGGED: ModerationFlaggedEvent,
    EventName.MATCH_DECISION: MatchDecisionEvent,
    EventName.DELIVERY_ATTEMPTED: DeliveryAttemptedEvent,
    EventName.ACK_RECEIVED: AckReceivedEvent,
    EventName.CRISIS_BLOCKED: CrisisBlockedEvent,
}


@dataclass(frozen=True)
class EventRecord:
    name: EventName
    payload: EventPayload


class EventEmitter(Protocol):
    def emit(self, name: EventName, payload: EventPayload) -> None:
        ...


class InMemoryEventStore:
    def __init__(self) -> None:
        self.records: List[EventRecord] = []

    def emit(self, name: EventName, payload: EventPayload) -> None:
        self.records.append(EventRecord(name=name, payload=payload))


_default_store = InMemoryEventStore()


def get_event_emitter() -> EventEmitter:
    return _default_store


def new_request_id() -> str:
    return str(uuid.uuid4())


def validate_event(name: EventName, payload: dict) -> EventPayload:
    schema = EVENT_SCHEMAS[name]
    return schema(**payload)


def safe_emit(emitter: EventEmitter, name: EventName, payload: dict) -> None:
    try:
        validated = validate_event(name, payload)
    except ValidationError as exc:
        raise ValueError("Invalid event payload") from exc
    emitter.emit(name, validated)
