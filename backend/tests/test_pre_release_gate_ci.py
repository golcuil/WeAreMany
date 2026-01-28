from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import pre_release_gate_ci  # noqa: E402


def test_pre_release_gate_missing_env(monkeypatch, capsys):
    monkeypatch.setattr(pre_release_gate_ci, "_run", lambda _: 1)
    exit_code = pre_release_gate_ci.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "pre_release_gate status=fail reason=missing_env"


def test_pre_release_gate_ok(monkeypatch, capsys):
    monkeypatch.setattr(pre_release_gate_ci, "_run", lambda _: 0)
    exit_code = pre_release_gate_ci.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "pre_release_gate status=ok"
