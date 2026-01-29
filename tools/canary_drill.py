from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess

from tools.cli_contract import add_common_flags, emit_output, help_epilog
SECRET_PATTERN = re.compile(
    r"(postgresql?://|BEGIN PRIVATE KEY|Authorization: Bearer|\bsk-[A-Za-z0-9]{8,})"
)


def _print(state: str, reason: str | None, as_json: bool) -> int:
    return emit_output(
        "canary_drill",
        {"state": state, "reason": reason},
        allowlist={"state", "reason", "status"},
        as_json=as_json,
        order=["state", "reason"],
    )


def _run(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _has_secret(text: str) -> bool:
    return bool(SECRET_PATTERN.search(text))


def _parse_status(line: str, prefix: str) -> tuple[str | None, str | None]:
    pattern = rf"{re.escape(prefix)} status=(\w+)(?: reason=([\w_]+))?"
    match = re.search(pattern, line)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _write_summary(state: str, reason: str | None, canary_status: str | None) -> None:
    os.makedirs("artifacts", exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "reason": reason,
        "baseline_id": None,
        "canary_gate_status": canary_status,
    }
    path = os.path.join("artifacts", "canary_drill_summary.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), sort_keys=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Canary drill rehearsal.",
        epilog=help_epilog("canary_drill", ["0 hold/ready", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_common_flags(parser)
    args = parser.parse_args(argv)

    code, stdout, stderr = _run(
        ["python3", "-m", "tools.baseline_validate", "--latest"]
    )
    if _has_secret(stdout) or _has_secret(stderr):
        _print("fail", "secret_echo_detected", args.json)
        _write_summary("fail", "secret_echo_detected", None)
        return 1
    status, reason = _parse_status(stdout, "baseline_validate")
    if status is None:
        _print("fail", "unexpected_output_format", args.json)
        _write_summary("fail", "unexpected_output_format", None)
        return 1
    if status != "ok":
        hold_reason = reason or "baseline_not_ready"
        _print("hold", hold_reason, args.json)
        _write_summary("hold", hold_reason, None)
        return 0

    code, stdout, stderr = _run(["python3", "-m", "tools.canary_gate"])
    if _has_secret(stdout) or _has_secret(stderr):
        _print("fail", "secret_echo_detected", args.json)
        _write_summary("fail", "secret_echo_detected", None)
        return 1
    status, reason = _parse_status(stdout, "canary_gate")
    if status is None:
        _print("fail", "unexpected_output_format", args.json)
        _write_summary("fail", "unexpected_output_format", None)
        return 1

    if status != "ok":
        hold_reason = reason or "canary_hold"
        _print("hold", hold_reason, args.json)
        _write_summary("hold", hold_reason, status)
        return 0

    _print("ready", None, args.json)
    _write_summary("ready", None, status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
