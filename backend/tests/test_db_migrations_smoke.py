import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_migrations_smoke  # noqa: E402


def test_db_migrations_smoke_missing_dsn(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN_TEST", raising=False)
    exit_code = db_migrations_smoke.main(["--dsn-env", "POSTGRES_DSN_TEST"])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "db_migrations_smoke status=fail reason=missing_dsn_env"


def test_db_migrations_smoke_no_secret_echo(monkeypatch, capsys):
    secret = "postgres://example-secret"
    monkeypatch.setenv("POSTGRES_DSN_TEST", secret)
    monkeypatch.setattr(db_migrations_smoke, "_run_db_bootstrap", lambda *_: 0)
    monkeypatch.setattr(db_migrations_smoke, "_run_db_verify", lambda *_: 0)
    exit_code = db_migrations_smoke.main(["--dsn-env", "POSTGRES_DSN_TEST"])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert secret not in output
