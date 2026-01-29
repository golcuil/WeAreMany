from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess

from tools.cli_contract import add_common_flags, emit_output, help_epilog

ALLOWED_STEPS = {
    "docs_consistency_check": {("ok", None)},
    "policy_check": {("ok", None)},
    "db_bootstrap_dry_run": {("ok", None)},
    "db_verify": {("ok", None), ("not_configured", "missing_dsn")},
    "prod_config_contract": {("ok", None), ("fail", "missing_env")},
    "prod_verify": {("ok", None), ("not_configured", "missing_required_env")},
    "baseline_validate": {
        ("ok", None),
        ("fail", "missing_latest_pointer"),
        ("fail", "latest_pointer_missing_target"),
    },
    "canary_drill": {
        ("ready", None),
        ("hold", "missing_latest_pointer"),
        ("hold", "hold_not_configured"),
        ("hold", "hold_insufficient_data"),
    },
    "secret_echo_guard": {("ok", None)},
}


def _print(status: str, reason: str | None, as_json: bool) -> int:
    return emit_output(
        "operator_rehearsal",
        {"status": status, "reason": reason},
        allowlist={"status", "reason"},
        as_json=as_json,
        order=["status", "reason"],
    )


def _run_command(cmd: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend:."
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip()


def _parse_status(line: str, prefix: str) -> tuple[str | None, str | None]:
    pattern = rf"{re.escape(prefix)} status=(\w+)(?: reason=([\w_]+))?"
    match = re.search(pattern, line)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _parse_state(line: str, prefix: str) -> tuple[str | None, str | None]:
    pattern = rf"{re.escape(prefix)} state=(\w+)(?: reason=([\w_]+))?"
    match = re.search(pattern, line)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _step_result(step: str, status: str | None, reason: str | None) -> tuple[bool, dict]:
    allowed = ALLOWED_STEPS.get(step, set())
    token = (status, reason)
    if token in allowed:
        return True, {"status": status, "reason": reason}
    return False, {"status": status, "reason": reason}


def _run_step(step: str, cmd: list[str], parser: str, prefix: str) -> tuple[bool, dict]:
    code, stdout = _run_command(cmd)
    if parser == "status":
        status, reason = _parse_status(stdout, prefix)
    elif parser == "state":
        status, reason = _parse_state(stdout, prefix)
    elif parser == "policy_check":
        status, reason = ("ok", None) if code == 0 else ("fail", "policy_check_failed")
    else:
        status, reason = None, None

    if status is None:
        return False, {"status": "fail", "reason": "unexpected_output_format"}
    ok, payload = _step_result(step, status, reason)
    return ok, payload


def _write_summary(path: str, summary: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, separators=(",", ":"), sort_keys=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Operator no-secrets rehearsal.",
        epilog=help_epilog("operator_rehearsal", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--out",
        default=os.path.join("artifacts", "operator_rehearsal_summary.json"),
    )
    add_common_flags(parser)
    args = parser.parse_args(argv)

    steps = []

    ok, payload = _run_step(
        "docs_consistency_check",
        ["python3", "-m", "tools.docs_consistency_check"],
        "status",
        "docs_check",
    )
    steps.append(("docs_consistency_check", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "policy_check", ["python3", "tools/policy_check.py"], "policy_check", "policy_check"
    )
    steps.append(("policy_check", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "db_bootstrap_dry_run",
        ["python3", "-m", "tools.db_bootstrap", "--dry-run"],
        "status",
        "db_bootstrap_dry_run",
    )
    steps.append(("db_bootstrap_dry_run", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "db_verify",
        ["python3", "-m", "tools.db_verify"],
        "status",
        "db_verify",
    )
    steps.append(("db_verify", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "prod_config_contract",
        ["python3", "-m", "tools.prod_config_contract"],
        "status",
        "prod_config",
    )
    steps.append(("prod_config_contract", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "prod_verify",
        ["python3", "-m", "tools.prod_verify"],
        "status",
        "prod_verify",
    )
    steps.append(("prod_verify", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "baseline_validate",
        ["python3", "-m", "tools.baseline_validate", "--latest"],
        "status",
        "baseline_validate",
    )
    steps.append(("baseline_validate", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    ok, payload = _run_step(
        "canary_drill",
        ["python3", "-m", "tools.canary_drill"],
        "state",
        "canary_drill",
    )
    steps.append(("canary_drill", payload))
    if not ok:
        _print("fail", "unexpected_step_token", args.json)
        return 1

    summary = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "steps": {name: data for name, data in steps},
    }
    _write_summary(args.out, summary)

    guard_code, guard_out = _run_command(["python3", "-m", "tools.secret_echo_guard"])
    guard_status, guard_reason = _parse_status(guard_out, "secret_echo_guard")
    if guard_code != 0 or (guard_status, guard_reason) not in ALLOWED_STEPS["secret_echo_guard"]:
        _print("fail", "secret_echo_guard_failed_after_artifact", args.json)
        return 1

    guard_code, guard_out = _run_command(["python3", "-m", "tools.secret_echo_guard"])
    guard_status, guard_reason = _parse_status(guard_out, "secret_echo_guard")
    if guard_code != 0 or (guard_status, guard_reason) not in ALLOWED_STEPS["secret_echo_guard"]:
        _print("fail", "secret_echo_guard_failed_final", args.json)
        return 1

    _print("ok", None, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
