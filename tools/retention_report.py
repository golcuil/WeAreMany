from __future__ import annotations

from datetime import datetime, timezone
import json
import os

from app.repository import get_repository
from tools.retention_policy import get_retention_days


def main() -> int:
    if not os.getenv("POSTGRES_DSN"):
        payload = {
            "status": "not_configured",
            "reason": "missing_dsn",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
        }
        print(f"retention_report {json.dumps(payload, separators=(',', ':'), sort_keys=True)}")
        return 0

    retention = get_retention_days()
    repo = get_repository()
    now = datetime.now(timezone.utc)
    try:
        report = repo.get_retention_report(now, retention)
    except Exception:
        payload = {
            "status": "fail",
            "reason": "report_failed",
            "ts_utc": now.isoformat(),
        }
        print(f"retention_report {json.dumps(payload, separators=(',', ':'), sort_keys=True)}")
        return 1

    drift = any(group["expired_rows"] > 0 for group in report.values())
    payload = {
        "status": "fail" if drift else "ok",
        "reason": "ttl_drift" if drift else "none",
        "ts_utc": now.isoformat(),
        "groups": report,
    }
    print(f"retention_report {json.dumps(payload, separators=(',', ':'), sort_keys=True)}")
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
