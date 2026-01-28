from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import re
import subprocess
from typing import Callable


SECRET_PATTERN = re.compile(
    r"(postgresql?://|BEGIN PRIVATE KEY|Authorization: Bearer|\bsk-[A-Za-z0-9]{8,})"
)
SNAPSHOT_PREFIX = "ops_metrics_snapshot "


@dataclass(frozen=True)
class StepResult:
    status: str
    reason: str | None = None


def _print(status: str, reason: str | None = None) -> None:
    line = f"canary_gate status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _run_command(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _has_secret(text: str) -> bool:
    return bool(SECRET_PATTERN.search(text))


def _parse_status(line: str, prefix: str) -> StepResult | None:
    pattern = rf"{re.escape(prefix)} status=(\w+)(?: reason=([\w_]+))?"
    match = re.search(pattern, line)
    if not match:
        return None
    status = match.group(1)
    reason = match.group(2)
    return StepResult(status=status, reason=reason)


def _extract_snapshot(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith(SNAPSHOT_PREFIX):
            return line[len(SNAPSHOT_PREFIX) :].strip()
    return None


def _write_summary(path: str, status: str, reason: str | None, steps: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": reason,
        "steps": steps,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), sort_keys=False)


def main(argv: list[str] | None = None, runner: Callable = _run_command) -> int:
    parser = argparse.ArgumentParser(description="Canary gate orchestration.")
    parser.add_argument(
        "--summary-out",
        default=os.path.join("artifacts", "canary_summary.json"),
    )
    args = parser.parse_args(argv)

    steps: dict[str, dict[str, str | None]] = {}

    code, stdout, stderr = runner(
        ["python3", "-m", "tools.prod_config_contract", "--mode=prod_required"]
    )
    if _has_secret(stdout) or _has_secret(stderr):
        _write_summary(args.summary_out, "fail", "secret_echo_detected", steps)
        _print("fail", "secret_echo_detected")
        return 1
    result = _parse_status(stdout, "prod_config")
    if code != 0:
        reason = result.reason if result and result.reason else "unexpected_output_format"
        steps["prod_config"] = {"status": "fail", "reason": reason}
        _write_summary(args.summary_out, "fail", reason, steps)
        _print("fail", reason)
        return 1
    steps["prod_config"] = {"status": "ok", "reason": None}

    code, stdout, stderr = runner(["python3", "-m", "tools.db_verify"])
    if _has_secret(stdout) or _has_secret(stderr):
        _write_summary(args.summary_out, "fail", "secret_echo_detected", steps)
        _print("fail", "secret_echo_detected")
        return 1
    result = _parse_status(stdout, "db_verify")
    if code != 0 or not result or result.status != "ok":
        steps["db_verify"] = {"status": "fail", "reason": "db_verify_failed"}
        _write_summary(args.summary_out, "fail", "db_verify_failed", steps)
        _print("fail", "db_verify_failed")
        return 1
    steps["db_verify"] = {"status": "ok", "reason": None}

    code, stdout, stderr = runner(["python3", "-m", "tools.ops_daily", "smoke"])
    if _has_secret(stdout) or _has_secret(stderr):
        _write_summary(args.summary_out, "fail", "secret_echo_detected", steps)
        _print("fail", "secret_echo_detected")
        return 1
    if code != 0:
        steps["ops_daily_smoke"] = {"status": "fail", "reason": "ops_daily_smoke_failed"}
        _write_summary(args.summary_out, "fail", "ops_daily_smoke_failed", steps)
        _print("fail", "ops_daily_smoke_failed")
        return 1
    steps["ops_daily_smoke"] = {"status": "ok", "reason": None}

    code, stdout, stderr = runner(
        ["python3", "-m", "tools.ops_daily", "metrics", "--days", "7"]
    )
    if _has_secret(stdout) or _has_secret(stderr):
        _write_summary(args.summary_out, "fail", "secret_echo_detected", steps)
        _print("fail", "secret_echo_detected")
        return 1
    snapshot = _extract_snapshot(stdout)
    if code != 0 or not snapshot:
        steps["metrics_snapshot"] = {
            "status": "fail",
            "reason": "missing_snapshot",
        }
        _write_summary(args.summary_out, "fail", "missing_snapshot", steps)
        _print("fail", "missing_snapshot")
        return 1
    snapshot_path = os.path.join(
        os.path.dirname(args.summary_out), "snapshot.json"
    )
    with open(snapshot_path, "w", encoding="utf-8") as handle:
        handle.write(snapshot)
    steps["metrics_snapshot"] = {"status": "ok", "reason": None}

    code, stdout, stderr = runner(
        ["python3", "-m", "tools.regression_gate", "--snapshot", snapshot_path]
    )
    if _has_secret(stdout) or _has_secret(stderr):
        _write_summary(args.summary_out, "fail", "secret_echo_detected", steps)
        _print("fail", "secret_echo_detected")
        return 1
    regression = _parse_status(stdout, "regression_gate")
    if not regression:
        steps["metrics_regression"] = {
            "status": "fail",
            "reason": "unexpected_output_format",
        }
        _write_summary(args.summary_out, "fail", "unexpected_output_format", steps)
        _print("fail", "unexpected_output_format")
        return 1
    if regression.status == "not_configured":
        steps["metrics_regression"] = {
            "status": "fail",
            "reason": "hold_not_configured",
        }
        _write_summary(args.summary_out, "fail", "hold_not_configured", steps)
        _print("fail", "hold_not_configured")
        return 1
    if regression.status == "insufficient_data" or code == 2:
        steps["metrics_regression"] = {
            "status": "fail",
            "reason": "hold_insufficient_data",
        }
        _write_summary(args.summary_out, "fail", "hold_insufficient_data", steps)
        _print("fail", "hold_insufficient_data")
        return 1
    if regression.status != "ok" or code != 0:
        steps["metrics_regression"] = {
            "status": "fail",
            "reason": "metrics_regression_failed",
        }
        _write_summary(args.summary_out, "fail", "metrics_regression_failed", steps)
        _print("fail", "metrics_regression_failed")
        return 1

    steps["metrics_regression"] = {"status": "ok", "reason": None}
    _write_summary(args.summary_out, "ok", None, steps)
    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
