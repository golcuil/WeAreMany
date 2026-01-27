from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from app.repository import get_repository
from tools.print_second_touch_metrics import SECOND_TOUCH_COUNTER_KEYS


@dataclass(frozen=True)
class SecondTouchHealthResult:
    exit_code: int
    status: str
    reason: str
    counters: Dict[str, int]
    held_rate: float
    suppressed_rate: float


def evaluate_second_touch_health(counters: Dict[str, int]) -> SecondTouchHealthResult:
    offers_generated = int(counters.get("offers_generated", 0))
    offers_suppressed_total = sum(
        int(counters.get(key, 0))
        for key in SECOND_TOUCH_COUNTER_KEYS
        if key.startswith("offers_suppressed_")
    )
    sends_attempted = int(counters.get("sends_attempted", 0))
    sends_held_total = sum(
        int(counters.get(key, 0))
        for key in SECOND_TOUCH_COUNTER_KEYS
        if key.startswith("sends_held_")
    )
    disables_identity_leak = int(counters.get("disables_identity_leak", 0))

    total_offers = offers_generated + offers_suppressed_total
    suppressed_rate = _safe_ratio(offers_suppressed_total, total_offers)
    held_rate = _safe_ratio(sends_held_total, max(sends_attempted, 1))

    if sends_attempted < 20 and offers_generated < 20:
        return SecondTouchHealthResult(
            exit_code=0,
            status="insufficient_data",
            reason="insufficient_volume",
            counters=counters,
            held_rate=held_rate,
            suppressed_rate=suppressed_rate,
        )
    if disables_identity_leak >= 1:
        return SecondTouchHealthResult(
            exit_code=2,
            status="unhealthy",
            reason="identity_leak_disable",
            counters=counters,
            held_rate=held_rate,
            suppressed_rate=suppressed_rate,
        )
    if sends_attempted >= 20 and held_rate > 0.35:
        return SecondTouchHealthResult(
            exit_code=2,
            status="unhealthy",
            reason="held_rate_high",
            counters=counters,
            held_rate=held_rate,
            suppressed_rate=suppressed_rate,
        )
    if total_offers >= 50 and suppressed_rate > 0.60:
        return SecondTouchHealthResult(
            exit_code=2,
            status="unhealthy",
            reason="suppressed_rate_high",
            counters=counters,
            held_rate=held_rate,
            suppressed_rate=suppressed_rate,
        )
    return SecondTouchHealthResult(
        exit_code=0,
        status="healthy",
        reason="ok",
        counters=counters,
        held_rate=held_rate,
        suppressed_rate=suppressed_rate,
    )


def format_second_touch_health(result: SecondTouchHealthResult, window_days: int) -> str:
    offers_generated = int(result.counters.get("offers_generated", 0))
    offers_suppressed_total = sum(
        int(result.counters.get(key, 0))
        for key in SECOND_TOUCH_COUNTER_KEYS
        if key.startswith("offers_suppressed_")
    )
    sends_attempted = int(result.counters.get("sends_attempted", 0))
    sends_queued = int(result.counters.get("sends_queued", 0))
    sends_held_total = sum(
        int(result.counters.get(key, 0))
        for key in SECOND_TOUCH_COUNTER_KEYS
        if key.startswith("sends_held_")
    )
    disables_identity_leak = int(result.counters.get("disables_identity_leak", 0))
    disables_negative_ack = int(result.counters.get("disables_negative_ack", 0))

    parts = [
        f"generated_at={datetime.now(timezone.utc).isoformat()}",
        f"second_touch_health_window_days={window_days}",
        f"offers_generated={offers_generated}",
        f"offers_suppressed_total={offers_suppressed_total}",
        f"offers_suppressed_rate={result.suppressed_rate:.2f}",
        f"sends_attempted={sends_attempted}",
        f"sends_queued={sends_queued}",
        f"sends_held_total={sends_held_total}",
        f"sends_held_rate={result.held_rate:.2f}",
        f"disables_identity_leak={disables_identity_leak}",
        f"disables_negative_ack={disables_negative_ack}",
        f"status={result.status}",
        f"reason={result.reason}",
    ]
    return " ".join(parts)


def run_second_touch_health(window_days: int = 7) -> SecondTouchHealthResult:
    repo = get_repository()
    counters = repo.get_second_touch_counters(window_days)
    return evaluate_second_touch_health(counters)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)
