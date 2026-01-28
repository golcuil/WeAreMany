from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import canary_gate  # noqa: E402


def _runner_factory(responses):
    def _runner(_cmd):
        return responses.pop(0)

    return _runner


def test_canary_gate_missing_env(tmp_path, capsys):
    responses = [
        (1, "prod_config status=fail reason=missing_env", ""),
    ]
    exit_code = canary_gate.main(
        ["--summary-out", str(tmp_path / "summary.json")],
        runner=_runner_factory(responses),
    )
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "canary_gate status=fail reason=missing_env"


def test_canary_gate_unexpected_output(tmp_path, capsys):
    responses = [
        (1, "garbage", ""),
    ]
    exit_code = canary_gate.main(
        ["--summary-out", str(tmp_path / "summary.json")],
        runner=_runner_factory(responses),
    )
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "canary_gate status=fail reason=unexpected_output_format"


def test_canary_gate_insufficient_data(tmp_path, capsys):
    responses = [
        (0, "prod_config status=ok", ""),
        (0, "db_verify status=ok", ""),
        (0, "generated_at=2026-01-01T00:00:00Z status=ok", ""),
        (
            0,
            "generated_at=2026-01-01T00:00:00Z\n"
            "ops_metrics_snapshot {\"delivered_total\":0}",
            "",
        ),
        (
            0,
            "metrics_regression status=insufficient_data reason=delivered_total_lt_min_n",
            "",
        ),
    ]
    exit_code = canary_gate.main(
        ["--summary-out", str(tmp_path / "summary.json")],
        runner=_runner_factory(responses),
    )
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "canary_gate status=fail reason=insufficient_data"


def test_canary_gate_ok(tmp_path, capsys):
    responses = [
        (0, "prod_config status=ok", ""),
        (0, "db_verify status=ok", ""),
        (0, "generated_at=2026-01-01T00:00:00Z status=ok", ""),
        (
            0,
            "generated_at=2026-01-01T00:00:00Z\n"
            "ops_metrics_snapshot {\"delivered_total\":50}",
            "",
        ),
        (0, "metrics_regression status=ok", ""),
    ]
    summary = tmp_path / "summary.json"
    exit_code = canary_gate.main(
        ["--summary-out", str(summary)],
        runner=_runner_factory(responses),
    )
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "canary_gate status=ok"
    assert summary.exists()
