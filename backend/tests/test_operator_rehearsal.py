import json
from pathlib import Path

from tools import operator_rehearsal


def test_operator_rehearsal_ok(monkeypatch, tmp_path, capsys):
    out_path = tmp_path / "summary.json"

    outputs = [
        (0, "docs_check status=ok"),
        (0, "ignored"),  # policy_check handled by exit code
        (0, "db_bootstrap_dry_run status=ok migrations=10"),
        (0, "db_verify status=not_configured reason=missing_dsn"),
        (1, "prod_config status=fail reason=missing_env missing=POSTGRES_DSN_PROD"),
        (0, "prod_verify status=not_configured reason=missing_required_env"),
        (1, "baseline_validate status=fail reason=missing_latest_pointer kind=latest"),
        (0, "canary_drill state=hold reason=hold_insufficient_data"),
        (0, "secret_echo_guard status=ok scanned=1"),
        (0, "secret_echo_guard status=ok scanned=1"),
    ]

    def fake_run(_cmd):
        return outputs.pop(0)

    monkeypatch.setattr(operator_rehearsal, "_run_command", fake_run)

    exit_code = operator_rehearsal.main(["--out", str(out_path)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output == "operator_rehearsal status=ok"
    payload = json.loads(out_path.read_text())
    assert payload["status"] == "ok"
    assert "postgres://user:pass@host/db" not in out_path.read_text()


def test_operator_rehearsal_unexpected_token(monkeypatch, tmp_path, capsys):
    out_path = tmp_path / "summary.json"
    outputs = [
        (0, "docs_check status=maybe"),
    ]

    monkeypatch.setattr(operator_rehearsal, "_run_command", lambda _cmd: outputs.pop(0))

    exit_code = operator_rehearsal.main(["--out", str(out_path)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "operator_rehearsal status=fail reason=unexpected_step_token"


def test_operator_rehearsal_guard_after_artifact(monkeypatch, tmp_path, capsys):
    out_path = tmp_path / "summary.json"
    outputs = [
        (0, "docs_check status=ok"),
        (0, "ignored"),  # policy_check
        (0, "db_bootstrap_dry_run status=ok migrations=10"),
        (0, "db_verify status=not_configured reason=missing_dsn"),
        (1, "prod_config status=fail reason=missing_env missing=POSTGRES_DSN_PROD"),
        (0, "prod_verify status=not_configured reason=missing_required_env"),
        (1, "baseline_validate status=fail reason=missing_latest_pointer kind=latest"),
        (0, "canary_drill state=hold reason=hold_insufficient_data"),
        (1, "secret_echo_guard status=fail reason=secret_detected"),
    ]

    monkeypatch.setattr(operator_rehearsal, "_run_command", lambda _cmd: outputs.pop(0))

    exit_code = operator_rehearsal.main(["--out", str(out_path)])
    output = capsys.readouterr().out.strip()
    assert exit_code == 1
    assert output == "operator_rehearsal status=fail reason=secret_echo_guard_failed_after_artifact"
