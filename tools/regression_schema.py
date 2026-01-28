from __future__ import annotations


BASELINE_KEYS = {
    "schema_version",
    "baseline_id",
    "created_at",
    "source_commit",
    "metrics",
    "status_tokens",
}

BASELINE_LATEST_KEYS = {
    "baseline_id",
    "baseline_filename",
    "created_at",
    "schema_version",
}

METRICS_KEYS = {
    "ts_utc",
    "window_days",
    "delivered_total",
    "ack_total",
    "ack_positive_total",
    "matching_health_h",
    "identity_leak_blocked_total",
    "crisis_routed_total",
    "p95_delivery_latency_s",
}


def validate_keys(payload: dict, allowed_keys: set[str]) -> bool:
    if not isinstance(payload, dict):
        return False
    keys = set(payload.keys())
    if keys != allowed_keys:
        return False
    return True


def validate_metrics(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    keys = set(payload.keys())
    return keys.issubset(METRICS_KEYS)


def validate_baseline(payload: dict) -> bool:
    if not validate_keys(payload, BASELINE_KEYS):
        return False
    if not validate_metrics(payload.get("metrics", {})):
        return False
    status_tokens = payload.get("status_tokens")
    if not isinstance(status_tokens, list):
        return False
    if not all(isinstance(item, str) for item in status_tokens):
        return False
    return True


def validate_baseline_latest(payload: dict) -> bool:
    return validate_keys(payload, BASELINE_LATEST_KEYS)
