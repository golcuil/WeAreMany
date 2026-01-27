from __future__ import annotations

import argparse
from datetime import datetime, timezone

from app.config import SECOND_TOUCH_EVENTS_RETENTION_DAYS
from app.repository import get_repository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cleanup second_touch events older than retention window."
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=SECOND_TOUCH_EVENTS_RETENTION_DAYS,
    )
    args = parser.parse_args(argv)

    repo = get_repository()
    now = datetime.now(timezone.utc)
    deleted = repo.cleanup_second_touch_events(args.retention_days, now)
    print(
        "second_touch_events_cleanup "
        f"retention_days={args.retention_days} "
        f"deleted_rows={deleted}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
