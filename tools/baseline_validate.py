from __future__ import annotations

import argparse
import json
import os

from tools.regression_schema import validate_baseline, validate_baseline_latest


def _print(status: str, reason: str | None = None, kind: str | None = None) -> None:
    line = f"baseline_validate status={status}"
    if reason:
        line = f"{line} reason={reason}"
    if kind:
        line = f"{line} kind={kind}"
    print(line)


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate regression baseline artifacts.")
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--latest", action="store_true")
    args = parser.parse_args(argv)

    if args.latest:
        latest_path = os.path.join("artifacts", "regression_baseline_latest.json")
        latest = _load_json(latest_path)
        if latest is None:
            _print("fail", "missing_latest_pointer", "latest")
            return 1
        if not validate_baseline_latest(latest):
            _print("fail", "invalid_baseline_schema", "latest")
            return 1
        baseline_path = os.path.join(
            os.path.dirname(latest_path),
            latest.get("baseline_filename", ""),
        )
        baseline = _load_json(baseline_path)
        if baseline is None:
            _print("fail", "latest_pointer_missing_target", "latest")
            return 1
        if not validate_baseline(baseline):
            _print("fail", "invalid_baseline_schema", "latest")
            return 1
        _print("ok", kind="latest")
        return 0

    if args.baseline:
        baseline = _load_json(args.baseline)
        if baseline is None:
            _print("fail", "missing_baseline", "baseline")
            return 1
        if not validate_baseline(baseline):
            _print("fail", "invalid_baseline_schema", "baseline")
            return 1
        _print("ok", kind="baseline")
        return 0

    _print("fail", "missing_args")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
