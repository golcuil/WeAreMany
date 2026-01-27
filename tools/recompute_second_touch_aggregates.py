from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from app.repository import get_repository


MAX_RECOMPUTE_DAYS = 30


def _print_line(
    days: int,
    days_written: int,
    recompute_partial: bool,
    reason: str | None = None,
) -> None:
    parts = [
        "second_touch_recompute",
        f"days={days}",
        f"days_written={days_written}",
        f"recompute_partial={str(recompute_partial).lower()}",
    ]
    if reason:
        parts.append(f"reason={reason}")
    print(" ".join(parts))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recompute second_touch daily aggregates for last N days."
    )
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args(argv)

    if args.days < 1 or args.days > MAX_RECOMPUTE_DAYS:
        print("second_touch_recompute status=fail reason=invalid_days")
        return 1

    now = datetime.now(timezone.utc)
    start_day = (now - timedelta(days=args.days - 1)).date()
    end_day = now.date()

    repo = get_repository()
    result = repo.recompute_second_touch_daily_aggregates(start_day, end_day)
    _print_line(
        args.days,
        int(result.get("days_written", 0)),
        bool(result.get("recompute_partial", False)),
        result.get("reason"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
