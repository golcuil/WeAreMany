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
    if "sqlstate=" in lowered:
        sqlstate = lowered.split("sqlstate=", 1)[1].split()[0]
        mapping = {
            "42p07": "duplicate_object",
            "42710": "duplicate_object",
            "23505": "unique_violation",
            "23503": "fk_violation",
            "3f000": "invalid_schema_or_db",
            "3d000": "invalid_schema_or_db",
            "42501": "insufficient_privilege",
            "0a000": "feature_not_supported",
        }
        return mapping.get(sqlstate, "sql_error")
    return "sql_error"


def _extract_token(output: str, key: str) -> str:
    if f"{key}=" not in output:
        return "unknown"
    return output.split(f"{key}=", 1)[1].split()[0]


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

    prereq_code, _prereq_output = _run(
        [
            "psql",
            dsn,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        ],
        env,
    )
    if prereq_code != 0:
        print("restore_dry_run status=fail reason=prereq_failed")
        return 1
    prereq_code, _prereq_output = _run(
        [
            "psql",
            dsn,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        ],
        env,
    )
    if prereq_code != 0:
        print("restore_dry_run status=fail reason=prereq_failed")
        return 1

    apply_code, apply_output = _run(
        [sys.executable, "-m", "tools.db_bootstrap", "apply_migrations"], env
    )
    if apply_code != 0:
        subreason = _classify_migration_failure(apply_output)
        migration = _extract_token(apply_output, "migration")
        sqlstate = _extract_token(apply_output, "sqlstate")
        print(
            "restore_dry_run status=fail reason=migrations_failed "
            f"subreason={subreason} migration={migration} sqlstate={sqlstate}"
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
        migration = _extract_token(idempotent_output, "migration")
        sqlstate = _extract_token(idempotent_output, "sqlstate")
        print(
            "restore_dry_run status=fail reason=idempotency_failed "
            f"subreason={subreason} migration={migration} sqlstate={sqlstate}"
        )
        return 1

    print("restore_dry_run status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
