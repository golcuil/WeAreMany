import hashlib
from dataclasses import dataclass
from typing import List, Optional, Protocol

import redis
from fastapi import HTTPException, status

from .config import MATCH_COOLDOWN_SECONDS, MATCH_MIN_POOL_K, REDIS_URL


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    intensity: str
    themes: List[str]


@dataclass(frozen=True)
class MatchDecision:
    decision: str
    reason: str
    recipient_id: Optional[str] = None
    system_generated_empathy: Optional[str] = None
    finite_content_bridge: Optional[str] = None
    crisis_action: Optional[str] = None


class DedupeStore(Protocol):
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        ...


class RedisDedupeStore:
    def __init__(self, client: redis.Redis):
        self._client = client

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"match:{sender_id}:{recipient_id}"
        return bool(self._client.set(key, "1", nx=True, ex=cooldown_seconds))


def get_dedupe_store() -> DedupeStore:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return RedisDedupeStore(client)


EMPATHY_TEMPLATES = [
    "This feeling can be heavy. You're not alone in it.",
    "Sometimes emotions feel intense and quiet at the same time.",
    "It's okay to sit with this feeling for a moment.",
]

FINITE_CONTENT_CATEGORIES = ["reflection", "grounding", "perspective"]


def _select_empathy(principal_id: str) -> str:
    digest = hashlib.sha256(principal_id.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(EMPATHY_TEMPLATES)
    return EMPATHY_TEMPLATES[idx]


def _select_content_bridge(principal_id: str) -> str:
    digest = hashlib.sha256((principal_id + "content").encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(FINITE_CONTENT_CATEGORIES)
    return FINITE_CONTENT_CATEGORIES[idx]


def _themes_compatible(sender_themes: List[str], candidate_themes: List[str]) -> bool:
    if not sender_themes or not candidate_themes:
        return True
    return bool(set(sender_themes) & set(candidate_themes))


def match_decision(
    principal_id: str,
    risk_level: int,
    intensity: str,
    themes: List[str],
    candidates: List[Candidate],
    dedupe_store: DedupeStore,
) -> MatchDecision:
    if risk_level == 2:
        return MatchDecision(
            decision="CRISIS_BLOCK",
            reason="risk_level_2",
            crisis_action="show_crisis",
        )

    if len(candidates) < MATCH_MIN_POOL_K:
        return MatchDecision(
            decision="HOLD",
            reason="insufficient_pool",
            system_generated_empathy=_select_empathy(principal_id),
            finite_content_bridge=_select_content_bridge(principal_id),
        )

    eligible = [
        candidate
        for candidate in candidates
        if candidate.intensity == intensity and _themes_compatible(themes, candidate.themes)
    ]
    if not eligible:
        return MatchDecision(decision="HOLD", reason="no_eligible_candidates")

    for candidate in eligible:
        if dedupe_store.allow_target(principal_id, candidate.candidate_id, MATCH_COOLDOWN_SECONDS):
            return MatchDecision(
                decision="DELIVER",
                reason="eligible",
                recipient_id=candidate.candidate_id,
            )

    return MatchDecision(decision="HOLD", reason="cooldown_active")
