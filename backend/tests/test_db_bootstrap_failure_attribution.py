import os
import tempfile
from pathlib import Path
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


def test_db_bootstrap_apply_failure_attribution(monkeypatch, capsys):
    dsn = os.getenv("POSTGRES_DSN_TEST")
    if not dsn:
        pytest.skip("POSTGRES_DSN_TEST not set")
    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg not available")

    test_db = _create_test_db(dsn, "wearemany_bootstrap_fail_attr")
    monkeypatch.setenv("POSTGRES_DSN_PROD", test_db)
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "0001_bad.sql"
        path = Path(tmpdir) / filename
        path.write_text("CREATE TABLE broken (id TEXT PRIMARY KEY;\n")
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: [filename])

        exit_code = db_bootstrap.main(["apply_migrations"])
        assert exit_code == 1
        output = capsys.readouterr().out.strip()
        assert output.startswith("db_bootstrap status=fail reason=migration_apply_failed")
        assert f"migration={filename}" in output
        assert "sqlstate=" in output
        assert "postgres://" not in output
        assert "\n" not in output
