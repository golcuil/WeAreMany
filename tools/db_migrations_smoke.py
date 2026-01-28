from __future__ import annotations

import argparse
import os
import subprocess


def _print(status: str, reason: str | None = None) -> None:
    line = f"db_migrations_smoke status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _run_db_bootstrap(dsn_env: str, command: str) -> tuple[int, str]:
    env = {**os.environ}
    env["POSTGRES_DSN_PROD"] = env.get(dsn_env, "")
    result = subprocess.run(
        ["python3", "-m", "tools.db_bootstrap", command],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, (result.stdout or "").strip()


def _run_db_verify(dsn_env: str) -> int:
    env = {**os.environ}
    env["POSTGRES_DSN_PROD"] = env.get(dsn_env, "")
    result = subprocess.run(
        ["python3", "-m", "tools.db_verify"],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply migrations + verify in CI.")
    parser.add_argument("--dsn-env", type=str, required=True)
    args = parser.parse_args(argv)

    if not os.getenv(args.dsn_env):
        _print("fail", "missing_dsn_env")
        return 1

    exit_code, output = _run_db_bootstrap(args.dsn_env, "apply_migrations")
    if exit_code != 0:
        subreason = "migration_apply_failed"
        if "reason=" in output:
            subreason = output.split("reason=", 1)[1].split()[0]
        _print("fail", f"apply_failed subreason={subreason}")
        return 1

    if _run_db_verify(args.dsn_env) != 0:
        _print("fail", "verify_failed")
        return 1

    exit_code, output = _run_db_bootstrap(args.dsn_env, "apply_migrations")
    if exit_code != 0:
        subreason = "migration_apply_failed"
        if "reason=" in output:
            subreason = output.split("reason=", 1)[1].split()[0]
        _print("fail", f"idempotency_failed subreason={subreason}")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
