from pathlib import Path

from tools import secret_echo_guard


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "secret_echo_guard"


def test_secret_echo_guard_detects_unsafe_fixtures(capsys, tmp_path):
    logs_dir = tmp_path / "logs"
    artifacts_dir = tmp_path / "artifacts"
    logs_dir.mkdir()
    artifacts_dir.mkdir()
    (logs_dir / "unsafe.log").write_text(
        (FIXTURES_DIR / "unsafe.log").read_text()
    )
    (artifacts_dir / "unsafe.json").write_text(
        (FIXTURES_DIR / "unsafe.json").read_text()
    )
    exit_code = secret_echo_guard.main(
        [
            "--log-dir",
            str(logs_dir),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output.startswith("secret_echo_guard status=fail reason=secret_detected")
    assert "postgres://user:pass@localhost:5432/app" not in output
    assert "Authorization: Bearer" not in output


def test_secret_echo_guard_allows_masked_values(capsys, tmp_path):
    logs_dir = tmp_path / "logs"
    artifacts_dir = tmp_path / "artifacts"
    logs_dir.mkdir()
    artifacts_dir.mkdir()
    (logs_dir / "safe.log").write_text(
        (FIXTURES_DIR / "safe.log").read_text()
    )
    (artifacts_dir / "safe.json").write_text(
        (FIXTURES_DIR / "safe.json").read_text()
    )
    exit_code = secret_echo_guard.main(
        [
            "--log-dir",
            str(logs_dir),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    )
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output.startswith("secret_echo_guard status=ok scanned=2")


def test_secret_echo_guard_single_line_output(capsys, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "log.log").write_text("status=ok\n")
    exit_code = secret_echo_guard.main(["--log-dir", str(logs_dir)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert "\n" not in output
