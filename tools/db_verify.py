from __future__ import annotations

import argparse
import os
from typing import Iterable

from tools.tool_contract import print_token_line
try:
    import psycopg as _psycopg
except Exception:
    _psycopg = None

psycopg = _psycopg


def _get_required_tables() -> list[str]:
    return [
        "mood_events",
        "messages",
        "inbox_items",
        "acknowledgements",
        "second_touch_pairs",
        "second_touch_offers",
        "second_touch_daily_aggregates",
    ]


def _check_tables(cur, required: Iterable[str]) -> bool:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
    )
    existing = {row[0] for row in cur.fetchall()}
    return all(name in existing for name in required)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify production DB connectivity and required tables.")
    parser.add_argument("--dsn-env", type=str, default="POSTGRES_DSN_PROD")
    args = parser.parse_args(argv)

    dsn = os.getenv(args.dsn_env)
    if not dsn:
        print_token_line(
            "db_verify",
            {"status": "not_configured", "reason": "missing_dsn"},
            order=["status", "reason"],
        )
        return 0
    if psycopg is None:
        print_token_line(
            "db_verify",
            {"status": "fail", "reason": "psycopg_missing"},
            order=["status", "reason"],
        )
        return 1

    try:
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            ok = _check_tables(cur, _get_required_tables())
    except Exception:
        print_token_line(
            "db_verify",
            {"status": "fail", "reason": "db_connect_failed"},
            order=["status", "reason"],
        )
        return 1

    if not ok:
        print_token_line(
            "db_verify",
            {"status": "fail", "reason": "missing_tables"},
            order=["status", "reason"],
        )
        return 1

    print_token_line("db_verify", {"status": "ok"}, order=["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
