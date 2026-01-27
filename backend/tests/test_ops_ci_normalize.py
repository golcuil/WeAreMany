import tempfile

from tools import ops_ci_normalize


def _write_log(text: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    handle.write(text)
    handle.flush()
    handle.close()
    return handle.name


def test_ops_ci_normalize_ok_exit(capsys):
    path = _write_log("status=healthy")
    exit_code = ops_ci_normalize.main(["--exit-code", "0", "--log-file", path])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "ops_ci_normalize status=ok reason=exit_0"


def test_ops_ci_normalize_insufficient_data(capsys):
    path = _write_log("ops_daily_watchdog status=insufficient_data reason=delivered_total_0")
    exit_code = ops_ci_normalize.main(["--exit-code", "2", "--log-file", path])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "ops_ci_normalize status=normalized reason=insufficient_data"


def test_ops_ci_normalize_unexpected_exit_two(capsys):
    path = _write_log("ops_daily_watchdog status=unhealthy")
    exit_code = ops_ci_normalize.main(["--exit-code", "2", "--log-file", path])
    assert exit_code == 2
    output = capsys.readouterr().out.strip()
    assert output == "ops_ci_normalize status=fail reason=unexpected_exit_2"


def test_ops_ci_normalize_exit_one(capsys):
    path = _write_log("some log")
    exit_code = ops_ci_normalize.main(["--exit-code", "1", "--log-file", path])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "ops_ci_normalize status=fail reason=exit_1"


def test_ops_ci_normalize_no_secret_echo(capsys):
    secret = "postgres://secret-value"
    path = _write_log(f"log {secret}")
    exit_code = ops_ci_normalize.main(["--exit-code", "2", "--log-file", path])
    assert exit_code == 2
    output = capsys.readouterr().out.strip()
    assert secret not in output
