from __future__ import annotations

import argparse
import json
import os

from tools.cli_contract import add_common_flags, emit_output, help_epilog
from tools.regression_schema import validate_baseline, validate_baseline_latest


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate regression baseline artifacts.",
        epilog=help_epilog("baseline_validate", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--baseline", type=str, default=None)
    parser.add_argument("--latest", action="store_true")
    add_common_flags(parser)
    args = parser.parse_args(argv)

    if args.latest:
        latest_path = os.path.join("artifacts", "regression_baseline_latest.json")
        latest = _load_json(latest_path)
        if latest is None:
            emit_output(
                "baseline_validate",
                {"status": "fail", "reason": "missing_latest_pointer", "kind": "latest"},
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        if not validate_baseline_latest(latest):
            emit_output(
                "baseline_validate",
                {"status": "fail", "reason": "invalid_baseline_schema", "kind": "latest"},
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        baseline_path = os.path.join(
            os.path.dirname(latest_path),
            latest.get("baseline_filename", ""),
        )
        baseline = _load_json(baseline_path)
        if baseline is None:
            emit_output(
                "baseline_validate",
                {
                    "status": "fail",
                    "reason": "latest_pointer_missing_target",
                    "kind": "latest",
                },
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        if not validate_baseline(baseline):
            emit_output(
                "baseline_validate",
                {"status": "fail", "reason": "invalid_baseline_schema", "kind": "latest"},
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        emit_output(
            "baseline_validate",
            {"status": "ok", "kind": "latest"},
            allowlist={"status", "reason", "kind"},
            as_json=args.json,
            order=["status", "kind"],
        )
        return 0

    if args.baseline:
        baseline = _load_json(args.baseline)
        if baseline is None:
            emit_output(
                "baseline_validate",
                {"status": "fail", "reason": "missing_baseline", "kind": "baseline"},
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        if not validate_baseline(baseline):
            emit_output(
                "baseline_validate",
                {"status": "fail", "reason": "invalid_baseline_schema", "kind": "baseline"},
                allowlist={"status", "reason", "kind"},
                as_json=args.json,
                order=["status", "reason", "kind"],
            )
            return 1
        emit_output(
            "baseline_validate",
            {"status": "ok", "kind": "baseline"},
            allowlist={"status", "reason", "kind"},
            as_json=args.json,
            order=["status", "kind"],
        )
        return 0

    emit_output(
        "baseline_validate",
        {"status": "fail", "reason": "missing_args"},
        allowlist={"status", "reason", "kind"},
        as_json=args.json,
        order=["status", "reason"],
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
