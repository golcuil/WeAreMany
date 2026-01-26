from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone

from app.repository import get_repository


@dataclass(frozen=True)
class HealthSnapshot:
    delivered_total: int
    positive_total: int
    ratio: float


def compute_health(delivered_total: int, positive_total: int) -> HealthSnapshot:
    ratio = (positive_total / delivered_total) if delivered_total else 0.0
    return HealthSnapshot(
        delivered_total=delivered_total,
        positive_total=positive_total,
        ratio=ratio,
    )


def evaluate_health(snapshot: HealthSnapshot, min_ratio: float) -> int:
    if snapshot.delivered_total == 0:
        return 2
    if snapshot.ratio < min_ratio:
        return 2
    return 0


def run_watchdog(days: int, min_ratio: float) -> int:
    repo = get_repository()
    aggregates = repo.list_daily_ack_aggregates(days)
    delivered_total = sum(item.delivered_count for item in aggregates)
    positive_total = sum(item.positive_ack_count for item in aggregates)
    snapshot = compute_health(delivered_total, positive_total)
    status = "healthy" if evaluate_health(snapshot, min_ratio) == 0 else "unhealthy"
    print(
        "generated_at="
        f"{datetime.now(timezone.utc).isoformat()} "
        f"window_days={days} delivered_total={snapshot.delivered_total} "
        f"positive_total={snapshot.positive_total} h={snapshot.ratio:.2f} "
        f"status={status}"
    )
    return evaluate_health(snapshot, min_ratio)


def main() -> int:
    parser = argparse.ArgumentParser(description="Matching health watchdog.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--min-ratio", type=float, default=0.2)
    args = parser.parse_args()
    return run_watchdog(args.days, args.min_ratio)


if __name__ == "__main__":
    raise SystemExit(main())
