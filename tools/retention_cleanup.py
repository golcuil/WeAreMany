from __future__ import annotations

from datetime import datetime, timezone

from app.repository import get_repository
from tools.retention_policy import get_retention_days


def main() -> int:
    retention = get_retention_days()
    repo = get_repository()
    now = datetime.now(timezone.utc)
    deleted_total = 0
    groups = [
        ("security_events", lambda: repo.prune_security_events(now, retention["security_events"])),
        (
            "second_touch_events",
            lambda: repo.cleanup_second_touch_events(retention["second_touch_events"], now),
        ),
        (
            "second_touch_daily_aggregates",
            lambda: repo.cleanup_second_touch_daily_aggregates(
                retention["second_touch_daily_aggregates"], now
            ),
        ),
        (
            "daily_ack_aggregates",
            lambda: repo.cleanup_daily_ack_aggregates(retention["daily_ack_aggregates"], now),
        ),
    ]
    try:
        for name, cleanup in groups:
            deleted = int(cleanup())
            deleted_total += deleted
            print(
                "retention_cleanup "
                f"table={name} status=ok deleted={deleted} cutoff_days={retention[name]}"
            )
    except Exception:
        print("retention_cleanup status=fail reason=exception")
        return 1
    print(
        "retention_cleanup "
        f"status=ok groups={len(groups)} deleted_total={deleted_total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
