from __future__ import annotations

import argparse
import os
import subprocess
import sys

from tools.cli_contract import add_common_flags, emit_output, help_epilog


def _run(cmd: list[str], env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    output = f"{result.stdout}\n{result.stderr}".strip()
    return result.returncode, output


def _parse_bootstrap_fail(output: str) -> dict[str, str] | None:
    for line in output.splitlines():
        if line.startswith("db_bootstrap status=fail"):
            tokens = {}
            for part in line.split():
                if "=" in part:
                    key, value = part.split("=", 1)
                    tokens[key] = value
            return tokens
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Restore dry-run against ephemeral Postgres.",
        epilog=help_epilog("restore_dry_run", ["0 ok", "1 fail"]),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--dsn-env", type=str, required=True)
    parser.add_argument(
        "--fixture",
        type=str,
        default="fixtures/sanitized_restore_fixture.sql",
    )
    add_common_flags(parser)
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        emit_output(
            "restore_dry_run",
            {
                "status": "fail",
                "reason": "migrations_failed",
                "subreason": "dsn_missing",
                "dsn_env": args.dsn_env,
            },
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason", "subreason", "dsn_env", "migration", "sqlstate"],
        )
        return 1
    if not os.path.exists(args.fixture):
        emit_output(
            "restore_dry_run",
            {"status": "fail", "reason": "missing_fixture"},
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    env = dict(os.environ)
    env["POSTGRES_DSN_PROD"] = dsn
    env["POSTGRES_DSN"] = dsn

    restore_code, _restore_output = _run(
        ["psql", dsn, "-v", "ON_ERROR_STOP=1", "-f", args.fixture],
        env,
    )
    if restore_code != 0:
        emit_output(
            "restore_dry_run",
            {"status": "fail", "reason": "restore_failed"},
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason"],
        )
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
        emit_output(
            "restore_dry_run",
            {"status": "fail", "reason": "prereq_failed"},
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason"],
        )
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
        emit_output(
            "restore_dry_run",
            {"status": "fail", "reason": "prereq_failed"},
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    apply_code, apply_output = _run(
        [sys.executable, "-m", "tools.db_bootstrap", "apply_migrations"], env
    )
    if apply_code != 0:
        parsed = _parse_bootstrap_fail(apply_output)
        if not parsed:
            emit_output(
                "restore_dry_run",
                {
                    "status": "fail",
                    "reason": "migrations_failed",
                    "subreason": "missing_bootstrap_fail_line",
                },
                allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
                as_json=args.json,
                order=["status", "reason", "subreason", "dsn_env", "migration", "sqlstate"],
            )
            return 1
        subreason = parsed.get("reason", "migration_apply_failed")
        migration = parsed.get("migration", "unknown")
        sqlstate = parsed.get("sqlstate", "na")
        emit_output(
            "restore_dry_run",
            {
                "status": "fail",
                "reason": "migrations_failed",
                "subreason": subreason,
                "migration": migration,
                "sqlstate": sqlstate,
            },
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason", "subreason", "dsn_env", "migration", "sqlstate"],
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
        emit_output(
            "restore_dry_run",
            {"status": "fail", "reason": "db_verify_failed"},
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason"],
        )
        return 1

    idempotent_code, idempotent_output = _run(
        [sys.executable, "-m", "tools.db_bootstrap", "apply_migrations"], env
    )
    if idempotent_code != 0:
        parsed = _parse_bootstrap_fail(idempotent_output)
        if not parsed:
            emit_output(
                "restore_dry_run",
                {
                    "status": "fail",
                    "reason": "idempotency_failed",
                    "subreason": "missing_bootstrap_fail_line",
                },
                allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
                as_json=args.json,
                order=["status", "reason", "subreason", "dsn_env", "migration", "sqlstate"],
            )
            return 1
        subreason = parsed.get("reason", "migration_apply_failed")
        migration = parsed.get("migration", "unknown")
        sqlstate = parsed.get("sqlstate", "na")
        emit_output(
            "restore_dry_run",
            {
                "status": "fail",
                "reason": "idempotency_failed",
                "subreason": subreason,
                "migration": migration,
                "sqlstate": sqlstate,
            },
            allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
            as_json=args.json,
            order=["status", "reason", "subreason", "dsn_env", "migration", "sqlstate"],
        )
        return 1

    emit_output(
        "restore_dry_run",
        {"status": "ok"},
        allowlist={"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
        as_json=args.json,
        order=["status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
