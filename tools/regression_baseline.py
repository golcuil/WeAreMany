from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import subprocess

from tools.regression_schema import (
    BASELINE_KEYS,
    BASELINE_LATEST_KEYS,
    METRICS_KEYS,
    validate_baseline,
    validate_baseline_latest,
    validate_metrics,
)


SNAPSHOT_PREFIX = "ops_metrics_snapshot "
ARTIFACTS_DIR = "artifacts"
SCHEMA_VERSION = 1


def _print(status: str, reason: str | None = None, baseline_id: str | None = None, path: str | None = None) -> None:
    line = f"regression_baseline status={status}"
    if reason:
        line = f"{line} reason={reason}"
    if baseline_id:
        line = f"{line} baseline_id={baseline_id}"
    if path:
        line = f"{line} path={path}"
    print(line)


def _run_ops_metrics() -> tuple[int, str, str]:
    result = subprocess.run(
        ["python3", "-m", "tools.ops_daily", "metrics", "--days", "7"],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _extract_snapshot(stdout: str) -> dict | None:
    for line in stdout.splitlines():
        if line.startswith(SNAPSHOT_PREFIX):
            payload = line[len(SNAPSHOT_PREFIX) :].strip()
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                return None
            if not validate_metrics(data):
                return None
            return data
    return None


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def _baseline_id(commit: str, timestamp: str) -> str:
    return f"{commit}-{timestamp}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate regression baseline.")
    parser.parse_args(argv)

    code, stdout, _ = _run_ops_metrics()
    if code != 0:
        _print("fail", "ops_metrics_failed")
        return 1

    snapshot = _extract_snapshot(stdout)
    if snapshot is None:
        _print("fail", "unexpected_output_format")
        return 1

    created_at = datetime.now(timezone.utc).isoformat()
    commit = _git_commit()
    compact_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    baseline_id = _baseline_id(commit, compact_ts)

    baseline = {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": baseline_id,
        "created_at": created_at,
        "source_commit": commit,
        "metrics": snapshot,
        "status_tokens": ["metrics_regression_pending"],
    }

    if not validate_baseline(baseline):
        _print("fail", "invalid_baseline_schema")
        return 1

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    baseline_filename = f"regression_baseline_{baseline_id}.json"
    baseline_path = os.path.join(ARTIFACTS_DIR, baseline_filename)
    with open(baseline_path, "w", encoding="utf-8") as handle:
        json.dump(baseline, handle, separators=(",", ":"), sort_keys=False)

    latest = {
        "baseline_id": baseline_id,
        "baseline_filename": baseline_filename,
        "created_at": created_at,
        "schema_version": SCHEMA_VERSION,
    }
    if not validate_baseline_latest(latest):
        _print("fail", "invalid_baseline_schema")
        return 1
    latest_path = os.path.join(ARTIFACTS_DIR, "regression_baseline_latest.json")
    with open(latest_path, "w", encoding="utf-8") as handle:
        json.dump(latest, handle, separators=(",", ":"), sort_keys=False)

    _print("ok", baseline_id=baseline_id, path=baseline_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
