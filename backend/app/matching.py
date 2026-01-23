import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

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


@dataclass(frozen=True)
class ProgressiveParams:
    intensity_band: int
    allow_theme_relax: bool
    pool_multiplier: float
    bucket: str


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
AFFINITY_ALPHA = 0.2


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
    intensity_band: int = 0,
    allow_theme_relax: bool = False,
    affinity_map: Optional[Dict[str, float]] = None,
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
        if _intensity_within_band(candidate.intensity, intensity, intensity_band)
        and _themes_compatible(themes, candidate.themes)
    ]
    if allow_theme_relax and not eligible:
        eligible = [
            candidate
            for candidate in candidates
            if _intensity_within_band(candidate.intensity, intensity, intensity_band)
        ]
    if not eligible:
        return MatchDecision(decision="HOLD", reason="no_eligible_candidates")

    eligible = _apply_affinity_bias(eligible, affinity_map)

    for candidate in eligible:
        if dedupe_store.allow_target(principal_id, candidate.candidate_id, MATCH_COOLDOWN_SECONDS):
            return MatchDecision(
                decision="DELIVER",
                reason="eligible",
                recipient_id=candidate.candidate_id,
            )

    return MatchDecision(decision="HOLD", reason="cooldown_active")


def progressive_params(health_ratio: float) -> ProgressiveParams:
    if health_ratio < 0.2:
        return ProgressiveParams(
            intensity_band=0,
            allow_theme_relax=False,
            pool_multiplier=-0.5,
            bucket="low",
        )
    if health_ratio > 0.6:
        return ProgressiveParams(
            intensity_band=2,
            allow_theme_relax=True,
            pool_multiplier=0.5,
            bucket="high",
        )
    return ProgressiveParams(
        intensity_band=0,
        allow_theme_relax=False,
        pool_multiplier=0.0,
        bucket="neutral",
    )


def _intensity_within_band(candidate: str, target: str, band: int) -> bool:
    levels = {"low": 0, "medium": 1, "high": 2}
    if candidate not in levels or target not in levels:
        return candidate == target
    return abs(levels[candidate] - levels[target]) <= band


def _apply_affinity_bias(
    candidates: List[Candidate],
    affinity_map: Optional[Dict[str, float]],
) -> List[Candidate]:
    if not affinity_map:
        return candidates
    max_score = max(affinity_map.values(), default=0.0)
    if max_score <= 0:
        return candidates

    scored = []
    for index, candidate in enumerate(candidates):
        weight = _affinity_weight(candidate, affinity_map, max_score)
        scored.append((-weight, index, candidate))
    scored.sort()
    return [item[2] for item in scored]


def _affinity_weight(
    candidate: Candidate,
    affinity_map: Dict[str, float],
    max_score: float,
) -> float:
    if not candidate.themes or max_score <= 0:
        return 1.0
    best = 0.0
    for theme in candidate.themes:
        score = affinity_map.get(theme, 0.0)
        if score > best:
            best = score
    if best <= 0:
        return 1.0
    normalized = min(best / max_score, 1.0)
    return 1.0 + (AFFINITY_ALPHA * normalized)
