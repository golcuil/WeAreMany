from pathlib import Path

from tools import secret_echo_guard


def test_secret_echo_guard_detects_dsn(capsys, tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("postgres://user:pass@host/db\n")
    exit_code = secret_echo_guard.main(["--log-file", str(log)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "secret_echo_guard status=fail reason=secret_detected"
    assert "postgres://user:pass@host/db" not in output


def test_secret_echo_guard_allows_masked_dsn(capsys, tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("***postgres://user:pass@host/db\n")
    exit_code = secret_echo_guard.main(["--log-file", str(log)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output.startswith("secret_echo_guard status=ok files=1")


def test_secret_echo_guard_private_key(capsys, tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("BEGIN PRIVATE KEY\n")
    exit_code = secret_echo_guard.main(["--log-file", str(log)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "secret_echo_guard status=fail reason=secret_detected"


def test_secret_echo_guard_single_line_output(capsys, tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("status=ok\n")
    exit_code = secret_echo_guard.main(["--log-file", str(log)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert "\n" not in output

