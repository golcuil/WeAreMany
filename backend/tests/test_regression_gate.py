from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import regression_gate  # noqa: E402


def test_regression_gate_missing_baseline(tmp_path, capsys):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"delivered_total": 0}))
    exit_code = regression_gate.main(
        [
            "--snapshot",
            str(snapshot),
            "--baseline-pointer",
            str(tmp_path / "missing.json"),
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "regression_gate status=not_configured reason=missing_baseline"


def test_regression_gate_insufficient_data(tmp_path, capsys, monkeypatch):
    pointer = tmp_path / "latest.json"
    baseline = tmp_path / "baseline.json"
    snapshot = tmp_path / "snapshot.json"
    pointer.write_text(
        json.dumps(
            {
                "baseline_id": "b1",
                "baseline_filename": baseline.name,
                "created_at": "2026-01-01T00:00:00Z",
                "schema_version": 1,
            }
        )
    )
    baseline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "baseline_id": "b1",
                "created_at": "2026-01-01T00:00:00Z",
                "source_commit": "abc",
                "metrics": {"delivered_total": 0},
                "status_tokens": ["metrics_regression_pending"],
            }
        )
    )
    snapshot.write_text(json.dumps({"delivered_total": 0}))
    monkeypatch.setattr(
        regression_gate,
        "_run_metrics_regression",
        lambda _path: (
            0,
            "metrics_regression status=insufficient_data reason=delivered_total_lt_min_n",
            "",
        ),
    )
    exit_code = regression_gate.main(
        [
            "--snapshot",
            str(snapshot),
            "--baseline-pointer",
            str(pointer),
        ]
    )
    assert exit_code == 2
    output = capsys.readouterr().out.strip()
    assert output == "regression_gate status=insufficient_data reason=delivered_total_lt_min_n"
