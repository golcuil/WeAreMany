from dataclasses import dataclass
from typing import Optional, Protocol


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


class Repository(Protocol):
    def save_mood(self, record: MoodRecord) -> None:
        ...

    def save_message(self, record: MessageRecord) -> None:
        ...


class NoopRepository:
    def save_mood(self, record: MoodRecord) -> None:
        return None

    def save_message(self, record: MessageRecord) -> None:
        return None


def get_repository() -> Repository:
    return NoopRepository()
