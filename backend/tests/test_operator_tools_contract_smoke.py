from __future__ import annotations

import json
from pathlib import Path

import tools.operator_tools_contract_smoke as smoke


def _json_line(tool: str, **fields: object) -> str:
    payload = {"tool": tool, "schema_version": 1}
    payload.update(fields)
    return json.dumps(payload, separators=(",", ":"))


def test_operator_tools_contract_smoke_ok(tmp_path):
    outputs = {}
    for name, spec in smoke.TOOL_SPECS.items():
        tool = name if name != "prod_config" else "prod_config"
        status = "ok"
        reason = None
        if name == "prod_config":
            status = "fail"
            reason = "missing_env"
        if name == "prod_verify":
            status = "not_configured"
            reason = "missing_required_env"
        if name == "db_verify":
            status = "not_configured"
            reason = "missing_dsn"
        if name == "baseline_validate":
            status = "fail"
            reason = "missing_latest_pointer"
        if name == "canary_drill":
            outputs[tuple(spec["cmd"])] = (
                0,
                _json_line(tool, state="hold", reason="hold_insufficient_data", status="hold"),
            )
            continue
        outputs[tuple(spec["cmd"])] = (
            0,
            _json_line(tool, status=status, reason=reason),
        )

    def runner(cmd):
        return outputs.get(tuple(cmd), (1, ""))

    out_path = tmp_path / "summary.json"
    code = smoke.main(["--out", str(out_path)], runner=runner)
    assert code == 0
    summary = json.loads(out_path.read_text())
    assert summary["status"] == "ok"
    assert "results" in summary
    assert "tools_run" in summary
    assert "postgres://" not in out_path.read_text()


def test_operator_tools_contract_smoke_unexpected_output(tmp_path):
    def runner(_cmd):
        return 0, ""

    out_path = tmp_path / "summary.json"
    code = smoke.main(["--out", str(out_path)], runner=runner)
    assert code == 1
