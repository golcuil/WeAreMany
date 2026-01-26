from __future__ import annotations

import argparse
from datetime import datetime, timezone

from app.repository import DailyAckAggregate, get_repository


def format_daily_ack_metrics(aggregates: list[DailyAckAggregate]) -> list[str]:
    lines: list[str] = []
    for record in aggregates:
        delivered = record.delivered_count
        positive = record.positive_ack_count
        ratio = (positive / delivered) if delivered else 0.0
        lines.append(
            f"{record.utc_day} delivered={delivered} positive={positive} h={ratio:.2f}"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Print daily acknowledgement metrics.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--theme", type=str, default=None)
    args = parser.parse_args()

    repo = get_repository()
    aggregates = repo.list_daily_ack_aggregates(args.days, theme_id=args.theme)
    lines = format_daily_ack_metrics(aggregates)
    print(f"generated_at={datetime.now(timezone.utc).isoformat()}")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
