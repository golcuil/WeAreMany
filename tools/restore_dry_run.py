from __future__ import annotations

import argparse
import os
import subprocess
import sys


def _run(cmd: list[str], env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    output = f"{result.stdout}\n{result.stderr}".strip()
    return result.returncode, output


def _classify_migration_failure(output: str) -> str:
    lowered = output.lower()
    if "migration_checksum_mismatch" in lowered:
        return "checksum_mismatch"
    if "already exists" in lowered or "relation" in lowered:
        return "duplicate_object"
    if "does not exist" in lowered or "missing table" in lowered:
        return "missing_table"
    return "sql_error"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore dry-run against ephemeral Postgres.")
    parser.add_argument("--dsn-env", type=str, default="POSTGRES_DSN_TEST")
    parser.add_argument(
        "--fixture",
        type=str,
        default="fixtures/sanitized_restore_fixture.sql",
    )
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        print("restore_dry_run status=fail reason=missing_dsn_env")
        return 1
    if not os.path.exists(args.fixture):
        print("restore_dry_run status=fail reason=missing_fixture")
        return 1

    env = dict(os.environ)
    env["POSTGRES_DSN"] = dsn

    restore_code, _restore_output = _run(
        ["psql", dsn, "-v", "ON_ERROR_STOP=1", "-f", args.fixture],
        env,
    )
    if restore_code != 0:
        print("restore_dry_run status=fail reason=restore_failed")
        return 1

    apply_code, apply_output = _run(
        [sys.executable, "-m", "tools.db_bootstrap", "apply_migrations"], env
    )
    if apply_code != 0:
        subreason = _classify_migration_failure(apply_output)
        print(
            "restore_dry_run status=fail reason=migrations_failed "
            f"subreason={subreason}"
        )
        return 1

    verify_code, _verify_output = _run(
        [
            sys.executable,
            "-m",
            "tools.db_verify",
            "--dsn-env",
            "POSTGRES_DSN",
        ],
        env,
    )
    if verify_code != 0:
        print("restore_dry_run status=fail reason=db_verify_failed")
        return 1

    idempotent_code, idempotent_output = _run(
        [sys.executable, "-m", "tools.db_bootstrap", "apply_migrations"], env
    )
    if idempotent_code != 0:
        subreason = _classify_migration_failure(idempotent_output)
        print(
            "restore_dry_run status=fail reason=idempotency_failed "
            f"subreason={subreason}"
        )
        return 1

    print("restore_dry_run status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
