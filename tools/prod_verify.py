from __future__ import annotations

import argparse
import os
import subprocess


def _print(status: str, reason: str | None = None) -> None:
    line = f"prod_verify status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _run(cmd: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend:."
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Production verification helper.")
    parser.add_argument("--mode", type=str, default="dry_run")
    parser.add_argument("--dsn-env", type=str, default="POSTGRES_DSN_PROD")
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        _print("not_configured", "missing_required_env")
        return 0

    code, _ = _run(["python3", "-m", "tools.db_bootstrap", "--dry-run"])
    if code != 0:
        _print("fail", "db_bootstrap_failed")
        return 1

    if args.mode == "verify":
        code, _ = _run(["python3", "-m", "tools.db_verify"])
        if code != 0:
            _print("fail", "db_verify_failed")
            return 1
        code, _ = _run(["python3", "-m", "tools.ops_daily", "smoke"])
        if code != 0:
            _print("fail", "ops_daily_failed")
            return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
