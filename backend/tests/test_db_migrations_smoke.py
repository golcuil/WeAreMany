import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_migrations_smoke  # noqa: E402


def _get_test_dsn():
    return os.getenv("POSTGRES_DSN_TEST")


def _create_test_db(dsn: str, name: str) -> str:
    import psycopg
    from psycopg import sql

    admin_dsn = dsn.rsplit("/", 1)[0] + "/postgres"
    with psycopg.connect(admin_dsn) as conn, conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return admin_dsn.rsplit("/", 1)[0] + f"/{name}"


def test_db_migrations_smoke_missing_dsn(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN_TEST", raising=False)
    exit_code = db_migrations_smoke.main(["--dsn-env", "POSTGRES_DSN_TEST"])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "db_migrations_smoke status=fail reason=missing_dsn_env"


def test_db_migrations_smoke_no_secret_echo(monkeypatch, capsys):
    secret = "postgres://example-secret"
    monkeypatch.setenv("POSTGRES_DSN_TEST", secret)
    monkeypatch.setattr(db_migrations_smoke, "_run_db_bootstrap", lambda *_: (0, ""))
    monkeypatch.setattr(db_migrations_smoke, "_run_db_verify", lambda *_: 0)
    exit_code = db_migrations_smoke.main(["--dsn-env", "POSTGRES_DSN_TEST"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert secret not in output


def test_db_migrations_smoke_idempotent_apply(monkeypatch, capsys):
    dsn = _get_test_dsn()
    if not dsn:
        import pytest

        pytest.skip("POSTGRES_DSN_TEST not set")
    try:
        import psycopg  # noqa: F401
    except Exception:
        import pytest

        pytest.skip("psycopg not available")
    test_db = _create_test_db(dsn, "wearemany_migrations_smoke")
    monkeypatch.setenv("POSTGRES_DSN_TEST", test_db)
    exit_code = db_migrations_smoke.main(["--dsn-env", "POSTGRES_DSN_TEST"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "db_migrations_smoke status=ok"
