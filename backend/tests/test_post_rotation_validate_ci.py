from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import post_rotation_validate_ci  # noqa: E402


def test_post_rotation_validate_missing_env(monkeypatch, capsys):
    monkeypatch.setattr(post_rotation_validate_ci, "_run", lambda _: 1)
    exit_code = post_rotation_validate_ci.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "post_rotation_validate status=fail reason=missing_env"


def test_post_rotation_validate_ok(monkeypatch, capsys):
    monkeypatch.setattr(post_rotation_validate_ci, "_run", lambda _: 0)
    exit_code = post_rotation_validate_ci.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "post_rotation_validate status=ok"
