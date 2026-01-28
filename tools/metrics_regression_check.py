from __future__ import annotations

import argparse
import json
import sys

MIN_N = 50
MIN_H = 0.2
MAX_IDENTITY_LEAK_RATE = 0.05
MAX_CRISIS_RATE = 0.2
MAX_P95_LATENCY_S = 5.0


def _print(status: str, reason: str | None = None) -> None:
    line = f"metrics_regression status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _load_snapshot(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Metrics regression checker.")
    parser.add_argument("--snapshot", type=str, required=True)
    args = parser.parse_args(argv)

    try:
        snapshot = _load_snapshot(args.snapshot)
    except FileNotFoundError:
        _print("fail", "missing_snapshot")
        return 1
    except json.JSONDecodeError:
        _print("fail", "invalid_snapshot")
        return 1

    delivered_total = snapshot.get("delivered_total", 0)
    if delivered_total < MIN_N:
        _print("insufficient_data", "delivered_total_lt_min_n")
        return 0

    matching_health_h = snapshot.get("matching_health_h")
    if matching_health_h is not None and matching_health_h < MIN_H:
        _print("fail", "matching_health_low")
        return 1

    identity_leak_total = snapshot.get("identity_leak_blocked_total")
    if identity_leak_total is not None:
        if (identity_leak_total / delivered_total) > MAX_IDENTITY_LEAK_RATE:
            _print("fail", "identity_leak_rate_high")
            return 1

    crisis_total = snapshot.get("crisis_routed_total")
    if crisis_total is not None:
        if (crisis_total / delivered_total) > MAX_CRISIS_RATE:
            _print("fail", "crisis_rate_high")
            return 1

    p95_latency = snapshot.get("p95_delivery_latency_s")
    if p95_latency is not None and p95_latency > MAX_P95_LATENCY_S:
        _print("fail", "latency_p95_high")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
