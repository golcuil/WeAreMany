from __future__ import annotations

import argparse
import os
import subprocess

from tools.cli_contract import add_common_flags, emit_output, help_epilog


def _run(cmd: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend:."
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Production verification helper.",
        epilog=help_epilog("prod_verify", ["0 ok/not_configured", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--mode", type=str, default="dry_run")
    parser.add_argument("--dsn-env", type=str, default="POSTGRES_DSN_PROD")
    add_common_flags(parser)
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        emit_output(
            "prod_verify",
            {"status": "not_configured", "reason": "missing_required_env"},
            allowlist={"status", "reason"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 0

    code, _ = _run(["python3", "-m", "tools.db_bootstrap", "--dry-run"])
    if code != 0:
        emit_output(
            "prod_verify",
            {"status": "fail", "reason": "db_bootstrap_failed"},
            allowlist={"status", "reason"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    if args.mode == "verify":
        code, _ = _run(["python3", "-m", "tools.db_verify"])
        if code != 0:
            emit_output(
                "prod_verify",
                {"status": "fail", "reason": "db_verify_failed"},
                allowlist={"status", "reason"},
                as_json=args.json,
                order=["status", "reason"],
            )
            return 1
        code, _ = _run(["python3", "-m", "tools.ops_daily", "smoke"])
        if code != 0:
            emit_output(
                "prod_verify",
                {"status": "fail", "reason": "ops_daily_failed"},
                allowlist={"status", "reason"},
                as_json=args.json,
                order=["status", "reason"],
            )
            return 1

    emit_output(
        "prod_verify",
        {"status": "ok"},
        allowlist={"status", "reason"},
        as_json=args.json,
        order=["status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
