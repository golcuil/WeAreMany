from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import regression_baseline  # noqa: E402


def test_regression_baseline_writes_files(monkeypatch, tmp_path, capsys):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 0, 0, 0, tzinfo=tz)

    def fake_run():
        return 0, (
            "generated_at=2026-01-01T00:00:00Z\n"
            "ops_metrics_snapshot {\"delivered_total\":50}"
        ), ""

    monkeypatch.setattr(regression_baseline, "_run_ops_metrics", fake_run)
    monkeypatch.setattr(regression_baseline, "_git_commit", lambda: "abc123")
    monkeypatch.setattr(regression_baseline, "ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setattr(regression_baseline, "datetime", FixedDatetime)
    exit_code = regression_baseline.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output.startswith("regression_baseline status=ok baseline_id=abc123-")
    latest = tmp_path / "regression_baseline_latest.json"
    assert latest.exists()
