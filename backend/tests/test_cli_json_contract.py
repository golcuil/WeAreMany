from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import tools.baseline_validate as baseline_validate
import tools.canary_drill as canary_drill
import tools.db_verify as db_verify
import tools.docs_consistency_check as docs_consistency_check
import tools.prod_config_contract as prod_config_contract
import tools.secret_echo_guard as secret_echo_guard
from tools.cli_contract import emit_output


SUSPICIOUS = [
    "postgres://",
    "postgresql://",
    "Authorization:",
    "BEGIN PRIVATE KEY",
    "Bearer ",
]


def _capture(func, *args, **kwargs) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = func(*args, **kwargs)
    return code, buf.getvalue().strip()


def _assert_single_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 1
    return lines[0]


def _assert_no_secrets(text: str) -> None:
    for token in SUSPICIOUS:
        assert token not in text


def _assert_json_line(line: str, allowlist: set[str]) -> None:
    data = json.loads(line)
    assert data["tool"]
    assert data["schema_version"]
    for key in data.keys():
        assert key in allowlist


def test_json_outputs():
    cases = [
        (docs_consistency_check.main, [], {"tool", "schema_version", "status", "reason"}),
        (secret_echo_guard.main, ["--log-dir", "logs"], {"tool", "schema_version", "status", "reason", "matches", "scanned", "file", "line", "rule"}),
        (db_verify.main, [], {"tool", "schema_version", "status", "reason"}),
        (prod_config_contract.main, [], {"tool", "schema_version", "status", "reason", "missing", "required"}),
        (baseline_validate.main, ["--latest"], {"tool", "schema_version", "status", "reason", "kind"}),
        (canary_drill.main, [], {"tool", "schema_version", "status", "state", "reason"}),
    ]
    for func, args, allowlist in cases:
        code, out = _capture(func, args + ["--json"])
        line = _assert_single_line(out)
        _assert_json_line(line, allowlist)
        _assert_no_secrets(out)


def test_help_text_contains_sections():
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            docs_consistency_check.main(["--help"])
    except SystemExit:
        pass
    text = buf.getvalue()
    assert "Output" in text
    assert "Exit codes" in text
    assert "Safety" in text


def test_emit_output_invalid_key():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = emit_output(
            "dummy_tool",
            {"status": "ok", "extra": "nope"},
            allowlist={"status"},
            as_json=False,
        )
    line = _assert_single_line(buf.getvalue().strip())
    assert "status=fail" in line
    assert "invalid_output_key" in line
    assert code == 1
