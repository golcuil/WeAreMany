from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import tools.baseline_validate as baseline_validate
import tools.canary_drill as canary_drill
import tools.canary_gate as canary_gate
import tools.db_bootstrap as db_bootstrap
import tools.db_verify as db_verify
import tools.docs_consistency_check as docs_consistency_check
import tools.operator_rehearsal as operator_rehearsal
import tools.prod_config_contract as prod_config_contract
import tools.prod_verify as prod_verify
import tools.regression_gate as regression_gate
import tools.restore_dry_run as restore_dry_run
import tools.secret_echo_guard as secret_echo_guard


SUSPICIOUS = [
    "postgres://",
    "postgresql://",
    "Authorization:",
    "BEGIN PRIVATE KEY",
    "Bearer ",
]


def _capture(func, *args, **kwargs) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = func(*args, **kwargs)
    return code, out.getvalue().strip(), err.getvalue().strip()


def _assert_single_line(output: str) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    assert len(lines) == 1
    return lines[0]


def _assert_no_secrets(text: str) -> None:
    for token in SUSPICIOUS:
        assert token not in text


def _assert_keys(line: str, prefix: str, allowlist: set[str]) -> None:
    parts = line.split()
    assert parts[0] == prefix
    for token in parts[1:]:
        assert "=" in token
        key, value = token.split("=", 1)
        assert key in allowlist
        assert value != ""


def test_simple_tool_outputs(tmp_path):
    code, out, err = _capture(docs_consistency_check.main, [])
    line = _assert_single_line(out)
    _assert_keys(line, "docs_check", {"status", "reason"})
    _assert_no_secrets(out + err)

    code, out, err = _capture(secret_echo_guard.main, [])
    line = _assert_single_line(out)
    _assert_keys(
        line,
        "secret_echo_guard",
        {"status", "reason", "matches", "scanned", "file", "line", "rule"},
    )
    _assert_no_secrets(out + err)

    code, out, err = _capture(db_bootstrap.main, ["--dry-run"])
    line = _assert_single_line(out)
    _assert_keys(line, "db_bootstrap_dry_run", {"status", "reason", "migrations"})
    _assert_no_secrets(out + err)

    code, out, err = _capture(db_verify.main, [])
    line = _assert_single_line(out)
    _assert_keys(line, "db_verify", {"status", "reason"})
    _assert_no_secrets(out + err)

    code, out, err = _capture(prod_config_contract.main, [])
    line = _assert_single_line(out)
    _assert_keys(line, "prod_config", {"status", "reason", "missing", "required"})
    _assert_no_secrets(out + err)

    code, out, err = _capture(prod_verify.main, [])
    line = _assert_single_line(out)
    _assert_keys(line, "prod_verify", {"status", "reason"})
    _assert_no_secrets(out + err)

    code, out, err = _capture(restore_dry_run.main, ["--dsn-env", "POSTGRES_DSN_TEST"])
    line = _assert_single_line(out)
    _assert_keys(
        line,
        "restore_dry_run",
        {"status", "reason", "subreason", "dsn_env", "migration", "sqlstate"},
    )
    _assert_no_secrets(out + err)

    code, out, err = _capture(baseline_validate.main, ["--latest"])
    line = _assert_single_line(out)
    _assert_keys(line, "baseline_validate", {"status", "reason", "kind"})
    _assert_no_secrets(out + err)

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"delivered_total": 0}))
    code, out, err = _capture(
        regression_gate.main,
        ["--snapshot", str(snapshot)],
    )
    line = _assert_single_line(out)
    _assert_keys(line, "regression_gate", {"status", "reason"})
    _assert_no_secrets(out + err)


def test_canary_gate_output_contract(tmp_path):
    outputs = [
        (0, "prod_config status=ok required=1", ""),
        (0, "db_verify status=ok", ""),
        (0, "generated_at=2024-01-01T00:00:00Z status=ok", ""),
        (
            0,
            'ops_metrics_snapshot {"ts_utc":"2024-01-01T00:00:00Z","window_days":7,"delivered_total":0,"ack_total":0,"ack_positive_total":0,"matching_health_h":0.0,"identity_leak_blocked_total":null,"crisis_routed_total":null,"p95_delivery_latency_s":null}',
            "",
        ),
        (0, "regression_gate status=ok", ""),
    ]

    def runner(_cmd):
        return outputs.pop(0)

    code, out, err = _capture(
        canary_gate.main,
        ["--summary-out", str(tmp_path / "canary_summary.json")],
        runner=runner,
    )
    line = _assert_single_line(out)
    _assert_keys(line, "canary_gate", {"status", "reason"})
    _assert_no_secrets(out + err)


def test_canary_drill_output_contract(monkeypatch, tmp_path):
    outputs = [
        (0, "baseline_validate status=fail reason=missing_latest_pointer", ""),
    ]

    def runner(_cmd):
        return outputs.pop(0)

    monkeypatch.setattr(canary_drill, "_run", runner)
    code, out, err = _capture(canary_drill.main, [])
    line = _assert_single_line(out)
    _assert_keys(line, "canary_drill", {"state", "reason"})
    _assert_no_secrets(out + err)


def test_operator_rehearsal_output_contract(monkeypatch, tmp_path):
    outputs = [
        (0, "docs_check status=ok"),
        (0, ""),
        (0, "db_bootstrap_dry_run status=ok migrations=16"),
        (0, "db_verify status=not_configured reason=missing_dsn"),
        (1, "prod_config status=fail reason=missing_env missing=POSTGRES_DSN_PROD"),
        (0, "prod_verify status=not_configured reason=missing_required_env"),
        (0, "baseline_validate status=fail reason=missing_latest_pointer"),
        (0, "canary_drill state=hold reason=missing_latest_pointer"),
        (0, "secret_echo_guard status=ok scanned=0"),
        (0, "secret_echo_guard status=ok scanned=0"),
    ]

    def runner(_cmd):
        return outputs.pop(0)

    monkeypatch.setattr(operator_rehearsal, "_run_command", runner)
    code, out, err = _capture(
        operator_rehearsal.main,
        ["--out", str(tmp_path / "operator_rehearsal_summary.json")],
    )
    line = _assert_single_line(out)
    _assert_keys(line, "operator_rehearsal", {"status", "reason"})
    _assert_no_secrets(out + err)
