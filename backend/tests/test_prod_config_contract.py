from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import prod_config_contract  # noqa: E402


def test_prod_config_missing_env(monkeypatch, capsys):
    monkeypatch.delenv("POSTGRES_DSN_PROD", raising=False)
    exit_code = prod_config_contract.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "prod_config status=fail reason=missing_env missing=POSTGRES_DSN_PROD"


def test_prod_config_ok(monkeypatch, capsys):
    monkeypatch.setenv("POSTGRES_DSN_PROD", "postgres://example")
    exit_code = prod_config_contract.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "prod_config status=ok required=1"
    assert "postgres://example" not in output
