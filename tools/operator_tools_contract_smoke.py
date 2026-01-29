from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tools.cli_contract import add_common_flags, emit_output, help_epilog


SUSPICIOUS = re.compile(
    r"(postgresql?://|Authorization:|BEGIN PRIVATE KEY|Bearer\s+|\\bsk-[A-Za-z0-9]{8,})",
    re.IGNORECASE,
)

TOOL_SPECS: dict[str, dict[str, object]] = {
    "docs_check": {
        "cmd": ["python3", "-m", "tools.docs_consistency_check", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason"},
        "allowed_status": {("ok", None)},
    },
    "secret_echo_guard": {
        "cmd": [
            "python3",
            "-m",
            "tools.secret_echo_guard",
            "--json",
            "--artifacts-dir",
            "artifacts",
        ],
        "allowlist": {
            "tool",
            "schema_version",
            "status",
            "reason",
            "matches",
            "scanned",
            "file",
            "line",
            "rule",
        },
        "allowed_status": {("ok", None)},
    },
    "db_verify": {
        "cmd": ["python3", "-m", "tools.db_verify", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason"},
        "allowed_status": {("ok", None), ("not_configured", "missing_dsn")},
    },
    "prod_verify": {
        "cmd": ["python3", "-m", "tools.prod_verify", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason"},
        "allowed_status": {("ok", None), ("not_configured", "missing_required_env")},
    },
    "prod_config": {
        "cmd": ["python3", "-m", "tools.prod_config_contract", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason", "missing", "required"},
        "allowed_status": {("ok", None), ("fail", "missing_env")},
    },
    "operator_rehearsal": {
        "cmd": ["python3", "-m", "tools.operator_rehearsal", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason"},
        "allowed_status": {("ok", None)},
    },
    "baseline_validate": {
        "cmd": ["python3", "-m", "tools.baseline_validate", "--latest", "--json"],
        "allowlist": {"tool", "schema_version", "status", "reason", "kind"},
        "allowed_status": {
            ("ok", None),
            ("fail", "missing_latest_pointer"),
            ("fail", "latest_pointer_missing_target"),
        },
    },
    "canary_drill": {
        "cmd": ["python3", "-m", "tools.canary_drill", "--json"],
        "allowlist": {"tool", "schema_version", "status", "state", "reason"},
        "allowed_status": {
            ("ready", None),
            ("hold", "missing_latest_pointer"),
            ("hold", "hold_not_configured"),
            ("hold", "hold_insufficient_data"),
        },
        "status_key": "state",
    },
}


def _run(cmd: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend:."
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip()


def _single_line(output: str) -> str | None:
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) != 1:
        return None
    return lines[0]


def _parse_json(line: str, allowlist: set[str]) -> dict | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if any(key not in allowlist for key in data.keys()):
        return None
    if SUSPICIOUS.search(line):
        return None
    return data


def _run_tool(name: str, spec: dict[str, object], runner=_run) -> tuple[bool, dict]:
    code, output = runner(spec["cmd"])
    line = _single_line(output)
    if not line:
        return False, {"status": "fail", "reason": "unexpected_output_format"}
    parsed = _parse_json(line, spec["allowlist"])
    if not parsed:
        return False, {"status": "fail", "reason": "invalid_json_schema"}
    status_key = spec.get("status_key", "status")
    status = parsed.get(status_key)
    reason = parsed.get("reason")
    if (status, reason) not in spec["allowed_status"]:
        return False, {"status": "fail", "reason": "unexpected_step_token"}
    if code not in (0, 1, 2) and status != "ok":
        return False, {"status": "fail", "reason": "unexpected_exit_code"}
    return True, {"status": status, "reason": reason}


def _write_summary(path: str, results: dict[str, dict[str, object]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "tools_run": sorted(results.keys()),
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, separators=(",", ":"), sort_keys=False)


def main(argv: list[str] | None = None, runner=_run) -> int:
    parser = argparse.ArgumentParser(
        description="Manual operator tools contract smoke (no secrets).",
        epilog=help_epilog("operator_tools_contract_smoke", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--out",
        default=os.path.join("artifacts", "operator_tools_contract_smoke_summary.json"),
    )
    add_common_flags(parser)
    args = parser.parse_args(argv)

    results: dict[str, dict[str, object]] = {}
    for name, spec in TOOL_SPECS.items():
        ok, payload = _run_tool(name, spec, runner=runner)
        results[name] = payload
        if not ok:
            emit_output(
                "operator_tools_contract_smoke",
                {"status": "fail", "reason": payload.get("reason")},
                allowlist={"status", "reason"},
                as_json=args.json,
                order=["status", "reason"],
            )
            return 1

    _write_summary(args.out, results)
    guard_ok, _guard_payload = _run_tool(
        "secret_echo_guard",
        TOOL_SPECS["secret_echo_guard"],
        runner=runner,
    )
    if not guard_ok:
        emit_output(
            "operator_tools_contract_smoke",
            {"status": "fail", "reason": "secret_echo_guard_failed_after_artifact"},
            allowlist={"status", "reason"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    emit_output(
        "operator_tools_contract_smoke",
        {"status": "ok"},
        allowlist={"status", "reason"},
        as_json=args.json,
        order=["status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
