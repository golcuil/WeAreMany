import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_bootstrap  # noqa: E402


def test_db_bootstrap_dry_run_missing_dsn(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN_PROD", raising=False)
    exit_code = db_bootstrap.main(["dry_run"])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output.startswith("db_bootstrap status=fail mode=dry_run reason=dsn_missing")


def test_db_bootstrap_dry_run_psycopg_missing(monkeypatch, capsys):
    monkeypatch.setenv("POSTGRES_DSN_PROD", "postgres://example")
    monkeypatch.setattr(db_bootstrap, "_check_psycopg", lambda: False)
    exit_code = db_bootstrap.main(["dry_run"])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output.startswith(
        "db_bootstrap status=fail mode=dry_run reason=psycopg_missing"
    )
