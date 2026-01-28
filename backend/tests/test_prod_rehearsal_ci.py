import json
from pathlib import Path

from tools import prod_rehearsal_ci


def test_prod_rehearsal_missing_dsn(capsys, tmp_path, monkeypatch):
    monkeypatch.delenv("POSTGRES_DSN_TEST", raising=False)
    fixture = tmp_path / "fixture.sql"
    fixture.write_text("-- empty")
    exit_code = prod_rehearsal_ci.main(
        ["--dsn-env", "POSTGRES_DSN_TEST", "--restore-fixture", str(fixture)]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "prod_rehearsal status=fail reason=dsn_missing step=bootstrap_dry_run"


def test_prod_rehearsal_missing_fixture(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")
    exit_code = prod_rehearsal_ci.main(
        ["--dsn-env", "POSTGRES_DSN_TEST", "--restore-fixture", str(tmp_path / "no.sql")]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "prod_rehearsal status=fail reason=missing_fixture step=restore_dry_run"


def test_prod_rehearsal_ok(monkeypatch, tmp_path, capsys):
    fixture = tmp_path / "fixture.sql"
    fixture.write_text("-- empty")
    out_path = tmp_path / "summary.json"
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")
    monkeypatch.setattr(prod_rehearsal_ci, "_run_command", lambda *_: (0, "ok"))

    exit_code = prod_rehearsal_ci.main(
        [
            "--dsn-env",
            "POSTGRES_DSN_TEST",
            "--restore-fixture",
            str(fixture),
            "--out",
            str(out_path),
        ]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output == "prod_rehearsal status=ok steps=6"
    payload = json.loads(out_path.read_text())
    assert payload["summary"]["status"] == "ok"
    assert "postgres://user:pass@host/db" not in out_path.read_text()


def test_prod_rehearsal_secret_echo_detected(monkeypatch, tmp_path, capsys):
    fixture = tmp_path / "fixture.sql"
    fixture.write_text("-- empty")
    out_path = tmp_path / "summary.json"
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")
    monkeypatch.setattr(
        prod_rehearsal_ci, "_run_command", lambda *_: (0, "postgres://user:pass@host/db")
    )

    exit_code = prod_rehearsal_ci.main(
        [
            "--dsn-env",
            "POSTGRES_DSN_TEST",
            "--restore-fixture",
            str(fixture),
            "--out",
            str(out_path),
        ]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "prod_rehearsal status=fail reason=secret_echo_detected step=bootstrap_dry_run"
