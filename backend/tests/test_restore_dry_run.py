import os
from pathlib import Path

from tools import restore_dry_run


def test_restore_dry_run_missing_env(capsys, tmp_path, monkeypatch):
    monkeypatch.delenv("POSTGRES_DSN_TEST", raising=False)
    exit_code = restore_dry_run.main(["--fixture", str(tmp_path / "fixture.sql")])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "restore_dry_run status=fail reason=missing_dsn_env"


def test_restore_dry_run_missing_fixture(capsys, monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")
    exit_code = restore_dry_run.main(["--fixture", "fixtures/does_not_exist.sql"])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "restore_dry_run status=fail reason=missing_fixture"
    assert "postgres://user:pass@host/db" not in output


def test_restore_dry_run_single_line_output(capsys, monkeypatch, tmp_path):
    fixture = Path(tmp_path / "fixture.sql")
    fixture.write_text("-- empty")
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")

    monkeypatch.setattr(restore_dry_run, "_run", lambda *_args, **_kwargs: (0, ""))
    exit_code = restore_dry_run.main(["--fixture", str(fixture)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output == "restore_dry_run status=ok"
    assert "\n" not in output
    assert "postgres://user:pass@host/db" not in output


def test_restore_dry_run_propagates_migration_failure(capsys, monkeypatch, tmp_path):
    fixture = Path(tmp_path / "fixture.sql")
    fixture.write_text("-- empty")
    monkeypatch.setenv("POSTGRES_DSN_TEST", "postgres://user:pass@host/db")

    outputs = [
        (0, ""),  # restore fixture
        (0, ""),  # prereq pgcrypto
        (0, ""),  # prereq uuid-ossp
        (
            1,
            "db_bootstrap status=fail reason=migration_apply_failed "
            "migration=0002_bad.sql sqlstate=42601",
        ),
    ]

    def _fake_run(*_args, **_kwargs):
        return outputs.pop(0)

    monkeypatch.setattr(restore_dry_run, "_run", _fake_run)
    exit_code = restore_dry_run.main(["--fixture", str(fixture)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert (
        output
        == "restore_dry_run status=fail reason=migrations_failed "
        "subreason=migration_apply_failed migration=0002_bad.sql sqlstate=42601"
    )
