import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_verify  # noqa: E402


def test_db_verify_missing_dsn(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN_PROD", raising=False)
    exit_code = db_verify.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "db_verify status=not_configured reason=missing_dsn"


def test_db_verify_psycopg_missing(monkeypatch, capsys):
    monkeypatch.setenv("POSTGRES_DSN_PROD", "postgres://example")
    monkeypatch.setattr(db_verify, "psycopg", None, raising=False)
    exit_code = db_verify.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "db_verify status=fail reason=psycopg_missing"
    assert "postgres://example" not in output
