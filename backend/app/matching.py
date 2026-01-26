from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Protocol

try:
    import redis
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    redis = None

from .config import (
    AFFINITY_MAX_BIAS,
    AFFINITY_SCALE,
    MATCH_COOLDOWN_SECONDS,
    MATCH_MIN_POOL_K,
    REDIS_URL,
    MATCH_TUNING_ALLOW_THEME_RELAX_HIGH,
    MATCH_TUNING_HIGH_INTENSITY_BAND,
    MATCH_TUNING_INTENSITY_MAX,
    MATCH_TUNING_INTENSITY_MIN,
    MATCH_TUNING_LOW_INTENSITY_BAND,
    MATCH_TUNING_POOL_MAX,
    MATCH_TUNING_POOL_MIN,
    MATCH_TUNING_POOL_MULTIPLIER_HIGH,
    MATCH_TUNING_POOL_MULTIPLIER_LOW,
)
from .finite_content import select_finite_content
from .hold_reasons import HoldReason


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


@dataclass(frozen=True)
class MatchingTuning:
    low_intensity_band: int
    high_intensity_band: int
    pool_multiplier_low: float
    pool_multiplier_high: float
    allow_theme_relax_high: bool


def default_matching_tuning() -> MatchingTuning:
    return MatchingTuning(
        low_intensity_band=MATCH_TUNING_LOW_INTENSITY_BAND,
        high_intensity_band=MATCH_TUNING_HIGH_INTENSITY_BAND,
        pool_multiplier_low=MATCH_TUNING_POOL_MULTIPLIER_LOW,
        pool_multiplier_high=MATCH_TUNING_POOL_MULTIPLIER_HIGH,
        allow_theme_relax_high=MATCH_TUNING_ALLOW_THEME_RELAX_HIGH,
    )


class DedupeStore(Protocol):
    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        ...


class RedisDedupeStore:
    def __init__(self, client: redis.Redis):
        self._client = client

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"match:{sender_id}:{recipient_id}"
        return bool(self._client.set(key, "1", nx=True, ex=cooldown_seconds))


class InMemoryDedupeStore:
    def __init__(self) -> None:
        self._seen: Dict[str, datetime] = {}

    def allow_target(self, sender_id: str, recipient_id: str, cooldown_seconds: int) -> bool:
        key = f"{sender_id}:{recipient_id}"
        now = datetime.now(timezone.utc)
        expiry = self._seen.get(key)
        if expiry and expiry > now:
            return False
        self._seen[key] = now + timedelta(seconds=cooldown_seconds)
        return True


def get_dedupe_store() -> DedupeStore:
    if redis is None:
        return InMemoryDedupeStore()
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return RedisDedupeStore(client)


EMPATHY_TEMPLATES = [
    "This feeling can be heavy. You're not alone in it.",
    "Sometimes emotions feel intense and quiet at the same time.",
    "It's okay to sit with this feeling for a moment.",
]
AFFINITY_ALPHA = AFFINITY_SCALE


def _select_empathy(principal_id: str) -> str:
    digest = hashlib.sha256(principal_id.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(EMPATHY_TEMPLATES)
    return EMPATHY_TEMPLATES[idx]


def _select_content_bridge(
    valence: str,
    intensity: str,
    theme_tags: List[str],
) -> str:
    primary_theme = theme_tags[0] if theme_tags else None
    item = select_finite_content(valence, intensity, theme_id=primary_theme)
    return item.content_id


def _themes_compatible(sender_themes: List[str], candidate_themes: List[str]) -> bool:
    if not sender_themes or not candidate_themes:
        return True
    return bool(set(sender_themes) & set(candidate_themes))


def match_decision(
    principal_id: str,
    risk_level: int,
    intensity: str,
    valence: str,
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
            reason=HoldReason.RISK_LEVEL_2.value,
            crisis_action="show_crisis",
        )

    if len(candidates) < MATCH_MIN_POOL_K:
        return MatchDecision(
            decision="HOLD",
            reason=HoldReason.INSUFFICIENT_POOL.value,
            system_generated_empathy=_select_empathy(principal_id),
            finite_content_bridge=_select_content_bridge(valence, intensity, themes),
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
        return MatchDecision(decision="HOLD", reason=HoldReason.NO_ELIGIBLE_CANDIDATES.value)

    eligible = _apply_affinity_bias(eligible, affinity_map)

    for candidate in eligible:
        if dedupe_store.allow_target(principal_id, candidate.candidate_id, MATCH_COOLDOWN_SECONDS):
            return MatchDecision(
                decision="DELIVER",
                reason="eligible",
                recipient_id=candidate.candidate_id,
            )

    return MatchDecision(decision="HOLD", reason=HoldReason.COOLDOWN_ACTIVE.value)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def progressive_params(
    health_ratio: float,
    tuning: Optional[MatchingTuning] = None,
) -> ProgressiveParams:
    tuning = tuning or default_matching_tuning()
    if health_ratio < 0.2:
        intensity_band = int(
            _clamp(
                tuning.low_intensity_band,
                MATCH_TUNING_INTENSITY_MIN,
                MATCH_TUNING_INTENSITY_MAX,
            )
        )
        pool_multiplier = _clamp(
            tuning.pool_multiplier_low,
            MATCH_TUNING_POOL_MIN,
            MATCH_TUNING_POOL_MAX,
        )
        return ProgressiveParams(
            intensity_band=intensity_band,
            allow_theme_relax=False,
            pool_multiplier=pool_multiplier,
            bucket="low",
        )
    if health_ratio > 0.6:
        intensity_band = int(
            _clamp(tuning.high_intensity_band, MATCH_TUNING_INTENSITY_MIN, MATCH_TUNING_INTENSITY_MAX)
        )
        pool_multiplier = _clamp(
            tuning.pool_multiplier_high,
            MATCH_TUNING_POOL_MIN,
            MATCH_TUNING_POOL_MAX,
        )
        return ProgressiveParams(
            intensity_band=intensity_band,
            allow_theme_relax=tuning.allow_theme_relax_high,
            pool_multiplier=pool_multiplier,
            bucket="high",
        )
    return ProgressiveParams(
        intensity_band=MATCH_TUNING_LOW_INTENSITY_BAND,
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
    bias = _clamp(AFFINITY_ALPHA * normalized, 0.0, AFFINITY_MAX_BIAS)
    return 1.0 + bias
