from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import canary_drill  # noqa: E402


def _runner_factory(responses):
    def _runner(_cmd):
        return responses.pop(0)

    return _runner


def test_canary_drill_missing_pointer(tmp_path, capsys, monkeypatch):
    responses = [
        (1, "baseline_validate status=fail reason=missing_latest_pointer", ""),
    ]
    monkeypatch.setattr(canary_drill, "_run", _runner_factory(responses))
    monkeypatch.setattr(canary_drill, "os", __import__("os"))
    monkeypatch.chdir(tmp_path)
    exit_code = canary_drill.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "canary_drill state=hold reason=missing_latest_pointer"


def test_canary_drill_hold_insufficient(tmp_path, capsys, monkeypatch):
    responses = [
        (0, "baseline_validate status=ok kind=latest", ""),
        (1, "canary_gate status=fail reason=hold_insufficient_data", ""),
    ]
    monkeypatch.setattr(canary_drill, "_run", _runner_factory(responses))
    monkeypatch.chdir(tmp_path)
    exit_code = canary_drill.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "canary_drill state=hold reason=hold_insufficient_data"


def test_canary_drill_ready(tmp_path, capsys, monkeypatch):
    responses = [
        (0, "baseline_validate status=ok kind=latest", ""),
        (0, "canary_gate status=ok", ""),
    ]
    monkeypatch.setattr(canary_drill, "_run", _runner_factory(responses))
    monkeypatch.chdir(tmp_path)
    exit_code = canary_drill.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "canary_drill state=ready"


def test_canary_drill_unexpected_output(tmp_path, capsys, monkeypatch):
    responses = [
        (0, "baseline_validate status=ok kind=latest", ""),
        (1, "garbage", ""),
    ]
    monkeypatch.setattr(canary_drill, "_run", _runner_factory(responses))
    monkeypatch.chdir(tmp_path)
    exit_code = canary_drill.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "canary_drill state=fail reason=unexpected_output_format"
