from pathlib import Path
import tempfile
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import db_bootstrap  # noqa: E402


def _write_migrations(tmpdir: str, names: list[str]) -> None:
    for name in names:
        path = Path(tmpdir) / name
        path.write_text("-- migration\n")


def test_db_bootstrap_dry_run_ok(monkeypatch, capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["0001_init.sql", "0002_next.sql"]
        _write_migrations(tmpdir, files)
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: files)
        exit_code = db_bootstrap.main(["--dry-run"])
        assert exit_code == 0
        output = capsys.readouterr().out.strip()
        assert output == "db_bootstrap_dry_run status=ok migrations=2"


def test_db_bootstrap_dry_run_missing_migration(monkeypatch, capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["0001_init.sql", "0002_next.sql"]
        _write_migrations(tmpdir, ["0001_init.sql"])
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: files)
        exit_code = db_bootstrap.main(["--dry-run"])
        assert exit_code == 1
        output = capsys.readouterr().out.strip()
        assert output == "db_bootstrap_dry_run status=fail reason=missing_migration"


def test_db_bootstrap_dry_run_duplicate_id(monkeypatch, capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["0001_init.sql", "0001_dup.sql"]
        _write_migrations(tmpdir, files)
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: files)
        exit_code = db_bootstrap.main(["--dry-run"])
        assert exit_code == 1
        output = capsys.readouterr().out.strip()
        assert output == "db_bootstrap_dry_run status=fail reason=duplicate_migration_id"


def test_db_bootstrap_dry_run_non_increasing(monkeypatch, capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["0002_next.sql", "0001_init.sql"]
        _write_migrations(tmpdir, files)
        monkeypatch.setattr(db_bootstrap, "_migration_dir", lambda: tmpdir)
        monkeypatch.setattr(db_bootstrap, "_migration_files", lambda: files)
        exit_code = db_bootstrap.main(["--dry-run"])
        assert exit_code == 1
        output = capsys.readouterr().out.strip()
        assert output == "db_bootstrap_dry_run status=fail reason=non_increasing_migration_id"
