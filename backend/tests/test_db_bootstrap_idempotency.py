import os
import tempfile
from pathlib import Path
import re
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_bootstrap  # noqa: E402


def _create_test_db(dsn: str, name: str) -> str:
    import psycopg
    from psycopg import sql

    admin_dsn = dsn.rsplit("/", 1)[0] + "/postgres"
    with psycopg.connect(admin_dsn) as conn, conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return admin_dsn.rsplit("/", 1)[0] + f"/{name}"


def _write_migration(tmpdir: str, filename: str, table_name: str) -> None:
    path = Path(tmpdir) / filename
    path.write_text(f"CREATE TABLE {table_name} (id TEXT PRIMARY KEY);\n")


def _parse_counts(output: str) -> tuple[int, int]:
    applied = re.search(r"applied=(\d+)", output)
    skipped = re.search(r"skipped=(\d+)", output)
    assert applied and skipped
    return int(applied.group(1)), int(skipped.group(1))


def test_db_bootstrap_apply_idempotent(monkeypatch, capsys):
    dsn = os.getenv("POSTGRES_DSN_TEST")
    if not dsn:
        pytest.skip("POSTGRES_DSN_TEST not set")
    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg not available")

    test_db = _create_test_db(dsn, "wearemany_bootstrap_idempotent")
    monkeypatch.setenv("POSTGRES_DSN_PROD", test_db)
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "0001_init.sql"
        _write_migration(tmpdir, filename, "idempotent_table")
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: [filename])

        exit_code = db_bootstrap.main(["apply_migrations"])
        assert exit_code == 0
        output = capsys.readouterr().out.strip()
        applied, skipped = _parse_counts(output)
        assert applied == 1
        assert skipped == 0
        assert "postgres://" not in output

        exit_code = db_bootstrap.main(["apply_migrations"])
        assert exit_code == 0
        output = capsys.readouterr().out.strip()
        applied, skipped = _parse_counts(output)
        assert applied == 0
        assert skipped == 1


def test_db_bootstrap_checksum_mismatch(monkeypatch, capsys):
    dsn = os.getenv("POSTGRES_DSN_TEST")
    if not dsn:
        pytest.skip("POSTGRES_DSN_TEST not set")
    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg not available")

    test_db = _create_test_db(dsn, "wearemany_bootstrap_checksum")
    monkeypatch.setenv("POSTGRES_DSN_PROD", test_db)
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "0001_init.sql"
        path = Path(tmpdir) / filename
        path.write_text("CREATE TABLE checksum_table (id TEXT PRIMARY KEY);\n")
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: [filename])

        exit_code = db_bootstrap.main(["apply_migrations"])
        assert exit_code == 0
        capsys.readouterr()

        path.write_text("CREATE TABLE checksum_table (id TEXT PRIMARY KEY, v2 TEXT);\n")
        exit_code = db_bootstrap.main(["apply_migrations"])
        assert exit_code == 1
        output = capsys.readouterr().out.strip()
        assert "reason=migration_checksum_mismatch" in output
