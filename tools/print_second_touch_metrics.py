from __future__ import annotations

from typing import Dict


SECOND_TOUCH_COUNTER_KEYS = [
    "offers_generated",
    "offers_suppressed_rate_limited",
    "offers_suppressed_cooldown_active",
    "offers_suppressed_disabled_until_active",
    "offers_suppressed_disabled_permanent",
    "offers_suppressed_crisis_blocked",
    "offers_suppressed_unknown",
    "sends_attempted",
    "sends_queued",
    "sends_held_rate_limited",
    "sends_held_cooldown_active",
    "sends_held_disabled",
    "sends_held_crisis_window",
    "sends_held_identity_leak",
    "sends_held_offer_unavailable",
    "sends_held_risk_level_2",
    "disables_negative_ack",
    "disables_identity_leak",
]


def format_second_touch_metrics(counters: Dict[str, int], window_days: int) -> list[str]:
    safe_counts = {key: int(counters.get(key, 0)) for key in SECOND_TOUCH_COUNTER_KEYS}
    suppressed_total = sum(
        value
        for key, value in safe_counts.items()
        if key.startswith("offers_suppressed_")
    )
    held_total = sum(value for key, value in safe_counts.items() if key.startswith("sends_held_"))
    generated = safe_counts["offers_generated"]
    attempted = safe_counts["sends_attempted"]
    suppressed_rate = _safe_ratio(suppressed_total, generated + suppressed_total)
    held_rate = _safe_ratio(held_total, max(attempted, 1))

    parts = [f"second_touch_window_days={window_days}"]
    parts.append(f"offers_generated={generated}")
    parts.append(f"offers_suppressed_total={suppressed_total}")
    parts.append(f"offers_suppressed_rate={suppressed_rate:.2f}")
    for key in SECOND_TOUCH_COUNTER_KEYS:
        if key.startswith("offers_suppressed_") and key != "offers_suppressed_unknown":
            parts.append(f"{key}={safe_counts[key]}")
    parts.append(f"sends_attempted={attempted}")
    parts.append(f"sends_queued={safe_counts['sends_queued']}")
    parts.append(f"sends_held_total={held_total}")
    parts.append(f"sends_held_rate={held_rate:.2f}")
    for key in SECOND_TOUCH_COUNTER_KEYS:
        if key.startswith("sends_held_"):
            parts.append(f"{key}={safe_counts[key]}")
    parts.append(f"disables_negative_ack={safe_counts['disables_negative_ack']}")
    parts.append(f"disables_identity_leak={safe_counts['disables_identity_leak']}")

    return [" ".join(parts)]


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)
