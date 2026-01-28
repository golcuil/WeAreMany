from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone


def _run_command(cmd: list[str], env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    output = "\n".join([line for line in [stdout, stderr] if line]).strip()
    last_line = output.splitlines()[-1] if output else ""
    return result.returncode, last_line


def _detect_secret_echo(output: str, dsn: str) -> bool:
    if not output:
        return False
    lowered = output.lower()
    if "postgres://" in lowered or "postgresql://" in lowered:
        return True
    return dsn in output


def _fail(reason: str, step: str) -> tuple[int, dict[str, object]]:
    summary = {
        "status": "fail",
        "reason": reason,
        "step": step,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }
    print(f"prod_rehearsal status=fail reason={reason} step={step}")
    return 1, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run prod rehearsal against ephemeral Postgres.")
    parser.add_argument("--dsn-env", type=str, required=True)
    parser.add_argument("--restore-fixture", type=str, required=True)
    parser.add_argument("--out", type=str, default="rehearsal_summary.json")
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        exit_code, summary = _fail("dsn_missing", "bootstrap_dry_run")
        _write_summary(args.out, summary, steps={})
        return exit_code

    if not os.path.exists(args.restore_fixture):
        exit_code, summary = _fail("missing_fixture", "restore_dry_run")
        _write_summary(args.out, summary, steps={})
        return exit_code

    env = dict(os.environ)
    env["POSTGRES_DSN_PROD"] = dsn
    env["POSTGRES_DSN"] = dsn

    steps: dict[str, dict[str, object]] = {}

    step_plan = [
        ("bootstrap_dry_run", ["python3", "-m", "tools.db_bootstrap", "--dry-run"]),
        ("bootstrap_apply", ["python3", "-m", "tools.db_bootstrap", "apply_migrations"]),
        ("db_verify", ["python3", "-m", "tools.db_verify", "--dsn-env", "POSTGRES_DSN"]),
        ("bootstrap_idempotent", ["python3", "-m", "tools.db_bootstrap", "apply_migrations"]),
        (
            "restore_dry_run",
            [
                "python3",
                "-m",
                "tools.restore_dry_run",
                "--dsn-env",
                args.dsn_env,
                "--fixture",
                args.restore_fixture,
            ],
        ),
        ("ops_smoke", ["python3", "-m", "tools.ops_daily", "smoke"]),
    ]

    for name, cmd in step_plan:
        exit_code, output = _run_command(cmd, env)
        if _detect_secret_echo(output, dsn):
            exit_code, summary = _fail("secret_echo_detected", name)
            _write_summary(args.out, summary, steps=steps)
            return exit_code
        steps[name] = {"exit_code": exit_code, "output": output}
        if exit_code != 0:
            exit_code, summary = _fail("step_failed", name)
            _write_summary(args.out, summary, steps=steps)
            return exit_code

    summary = {
        "status": "ok",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "steps": {name: {"status": "ok"} for name in steps.keys()},
    }
    _write_summary(args.out, summary, steps=steps)
    print(f"prod_rehearsal status=ok steps={len(step_plan)}")
    return 0


def _write_summary(path: str, summary: dict[str, object], steps: dict[str, dict[str, object]]) -> None:
    payload = {
        "summary": summary,
        "steps": steps,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
