from __future__ import annotations

import os

RETENTION_DEFAULTS = {
    "security_events": 30,
    "second_touch_events": 90,
    "second_touch_daily_aggregates": 180,
    "daily_ack_aggregates": 180,
}

RETENTION_ENV = {
    "security_events": "SECURITY_EVENTS_RETENTION_DAYS",
    "second_touch_events": "SECOND_TOUCH_EVENTS_RETENTION_DAYS",
    "second_touch_daily_aggregates": "SECOND_TOUCH_AGG_RETENTION_DAYS",
    "daily_ack_aggregates": "DAILY_ACK_RETENTION_DAYS",
}

MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 365


def _parse_days(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        days = int(value)
    except ValueError:
        return default
    if days < MIN_RETENTION_DAYS:
        return MIN_RETENTION_DAYS
    if days > MAX_RETENTION_DAYS:
        return MAX_RETENTION_DAYS
    return days


def get_retention_days() -> dict[str, int]:
    values: dict[str, int] = {}
    for key, default in RETENTION_DEFAULTS.items():
        env_name = RETENTION_ENV[key]
        values[key] = _parse_days(os.getenv(env_name), default)
    return values
