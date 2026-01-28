from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from datetime import datetime, timezone

try:
    import psycopg as _psycopg
except Exception:
    _psycopg = None

psycopg = _psycopg


def _print_status(
    status: str,
    mode: str,
    reason: str | None = None,
    applied: int | None = None,
    skipped: int | None = None,
    migration: str | None = None,
    sqlstate: str | None = None,
) -> None:
    parts = [f"db_bootstrap status={status}", f"mode={mode}"]
    if reason:
        parts.append(f"reason={reason}")
    if applied is not None:
        parts.append(f"applied={applied}")
    if skipped is not None:
        parts.append(f"skipped={skipped}")
    if migration:
        parts.append(f"migration={migration}")
    if sqlstate:
        parts.append(f"sqlstate={sqlstate}")
    parts.append(f"generated_at={datetime.now(timezone.utc).isoformat()}")
    print(" ".join(parts))


def _check_dsn(env_name: str) -> str | None:
    return os.getenv(env_name)


def _check_psycopg() -> bool:
    return psycopg is not None


def _migration_dir() -> str:
    migration_dir = os.path.join(os.path.dirname(__file__), "..", "db", "migrations")
    return os.path.abspath(migration_dir)


def _migration_files() -> list[str]:
    return [
        "0001_init.sql",
        "0002_eligible_principals.sql",
        "0003_mood_events.sql",
        "0004_message_origin.sql",
        "0005_ack_reaction_expansion.sql",
        "0006_affinity_table.sql",
        "0007_messages_theme_tags.sql",
        "0008_mood_event_theme.sql",
        "0009_principal_crisis_state.sql",
        "0010_security_events.sql",
        "0011_matching_tuning.sql",
        "0012_finite_content_selections.sql",
        "0013_daily_ack_aggregates.sql",
        "0014_second_touch.sql",
        "0015_second_touch_daily_aggregates.sql",
        "0016_second_touch_events.sql",
    ]


def _validate_migration_plan(migration_dir: str, migration_files: list[str]) -> str | None:
    ids: list[int] = []
    for filename in migration_files:
        path = os.path.join(migration_dir, filename)
        if not os.path.exists(path):
            return "missing_migration"
        match = re.match(r"^(\d+)_", filename)
        if not match:
            return "invalid_migration_name"
        ids.append(int(match.group(1)))
    if len(set(ids)) != len(ids):
        return "duplicate_migration_id"
    if ids != sorted(ids):
        return "non_increasing_migration_id"
    return None


def _ensure_ledger(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def _load_migration(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _checksum(contents: str) -> str:
    return hashlib.sha256(contents.encode("utf-8")).hexdigest()


def _apply_migrations(dsn: str) -> tuple[bool, int, int, str | None, str | None, str | None]:
    migration_dir = _migration_dir()
    migration_files = _migration_files()
    if _validate_migration_plan(migration_dir, migration_files) is not None:
        return False, 0, 0, "migrations_invalid", None, None
    if psycopg is None:
        return False, 0, 0, "psycopg_missing", None, None

    applied = 0
    skipped = 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            _ensure_ledger(cur)
        for filename in migration_files:
            migration_id = filename.split("_", 1)[0]
            path = os.path.join(migration_dir, filename)
            contents = _load_migration(path)
            checksum = _checksum(contents)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT checksum FROM schema_migrations WHERE id = %s",
                    (migration_id,),
                )
                row = cur.fetchone()
                if row:
                    if row[0] != checksum:
                        conn.rollback()
                        return False, applied, skipped, "migration_checksum_mismatch", filename, "na"
                    skipped += 1
                    conn.commit()
                    continue
                try:
                    cur.execute(contents)
                    cur.execute(
                        """
                        INSERT INTO schema_migrations (id, filename, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (migration_id, filename, checksum),
                    )
                    conn.commit()
                    applied += 1
                except Exception as exc:
                    sqlstate = getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None)
                    if not sqlstate:
                        sqlstate = "na"
                    conn.rollback()
                    return False, applied, skipped, "migration_apply_failed", filename, sqlstate
    return True, applied, skipped, None, None, None


def _run_verify() -> bool:
    result = subprocess.run(
        ["python3", "-m", "tools.db_verify"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    return result.returncode == 0


def _run_bootstrap_dry_run() -> int:
    migration_dir = _migration_dir()
    migration_files = _migration_files()
    reason = _validate_migration_plan(migration_dir, migration_files)
    if reason:
        print(f"db_bootstrap_dry_run status=fail reason={reason}")
        return 1
    print(f"db_bootstrap_dry_run status=ok migrations={len(migration_files)}")
    return 0


def _run_apply(env_name: str) -> int:
    dsn = _check_dsn(env_name)
    if not dsn:
        _print_status("fail", "apply_migrations", "dsn_missing")
        return 1
    if not _check_psycopg():
        _print_status("fail", "apply_migrations", "psycopg_missing")
        return 1
    ok, applied, skipped, reason, migration, sqlstate = _apply_migrations(dsn)
    if not ok:
        _print_status(
            "fail",
            "apply_migrations",
            reason or "migrations_failed",
            migration=migration,
            sqlstate=sqlstate,
        )
        return 1
    _print_status("ok", "apply_migrations", applied=applied, skipped=skipped)
    return 0


def _run_verify_mode() -> int:
    if not _run_verify():
        _print_status("fail", "verify", "verify_failed")
        return 1
    _print_status("ok", "verify")
    return 0


def _run_all(env_name: str) -> int:
    if _run_apply(env_name) != 0:
        return 1
    if _run_verify_mode() != 0:
        return 1
    _print_status("ok", "all")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap production database.")
    parser.add_argument("--dsn-env", type=str, default="POSTGRES_DSN_PROD")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migration plan without DB connectivity.",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    subparsers.add_parser("dry_run")
    subparsers.add_parser("apply_migrations")
    subparsers.add_parser("verify")
    subparsers.add_parser("all")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        return _run_bootstrap_dry_run()

    if not args.command:
        _print_status("fail", "unknown", "invalid_command")
        return 1

    if args.command == "dry_run":
        return _run_bootstrap_dry_run()
    if args.command == "apply_migrations":
        return _run_apply(args.dsn_env)
    if args.command == "verify":
        return _run_verify_mode()
    if args.command == "all":
        return _run_all(args.dsn_env)
    _print_status("fail", "unknown", "invalid_command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
