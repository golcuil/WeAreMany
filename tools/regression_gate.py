from __future__ import annotations

import argparse
import json
import os
import re
import subprocess

from tools.regression_schema import validate_baseline, validate_baseline_latest, validate_metrics


SECRET_PATTERN = re.compile(r"(postgresql?://|BEGIN PRIVATE KEY|Authorization: Bearer|\bsk-[A-Za-z0-9]{8,})")


def _print(status: str, reason: str | None = None) -> None:
    line = f"regression_gate status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _has_secret(text: str) -> bool:
    return bool(SECRET_PATTERN.search(text))


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _run_metrics_regression(snapshot_path: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["python3", "-m", "tools.metrics_regression_check", "--snapshot", snapshot_path],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _parse_status(line: str, prefix: str) -> tuple[str | None, str | None]:
    pattern = rf"{re.escape(prefix)} status=(\w+)(?: reason=([\w_]+))?"
    match = re.search(pattern, line)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regression gate with baseline validation.")
    parser.add_argument("--snapshot", required=True, type=str)
    parser.add_argument(
        "--baseline-pointer",
        default=os.path.join("artifacts", "regression_baseline_latest.json"),
        type=str,
    )
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    pointer = _load_json(args.baseline_pointer)
    if pointer is None:
        _print("not_configured", "missing_baseline")
        return 1 if args.strict else 0
    if not validate_baseline_latest(pointer):
        _print("fail", "invalid_baseline_schema")
        return 1

    baseline_path = os.path.join(
        os.path.dirname(args.baseline_pointer),
        pointer.get("baseline_filename", ""),
    )
    baseline = _load_json(baseline_path)
    if baseline is None or not validate_baseline(baseline):
        _print("fail", "invalid_baseline_schema")
        return 1

    snapshot = _load_json(args.snapshot)
    if snapshot is None or not validate_metrics(snapshot):
        _print("fail", "invalid_snapshot")
        return 1

    code, stdout, stderr = _run_metrics_regression(args.snapshot)
    if _has_secret(stdout) or _has_secret(stderr):
        _print("fail", "secret_echo_detected")
        return 1
    status, reason = _parse_status(stdout, "metrics_regression")
    if status is None:
        _print("fail", "unexpected_output_format")
        return 1
    if status == "insufficient_data":
        _print("insufficient_data", reason or "delivered_total_lt_min_n")
        return 2
    if status != "ok" or code != 0:
        _print("fail", reason or "metrics_regression_failed")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
