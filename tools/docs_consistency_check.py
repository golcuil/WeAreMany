from __future__ import annotations

import argparse
import os
import re

REQUIRED_TOKENS = [
    "status=insufficient_data",
    "reason=missing_env",
    "db_bootstrap_dry_run",
    "db_verify status=not_configured",
]

MODULE_REFERENCES = [
    "tools.db_bootstrap",
    "tools.db_verify",
    "tools.ops_ci_normalize",
    "tools.prod_config_contract",
]

RUNBOOK_PATH = os.path.join("docs", "operator_runbook.md")

SUSPICIOUS_DSN = re.compile(r"postgres://[^\s:]+:[^\s@]+@")


def _print(status: str, reason: str | None = None) -> None:
    line = f"docs_check status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _load_runbook() -> str | None:
    if not os.path.exists(RUNBOOK_PATH):
        return None
    with open(RUNBOOK_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


def _module_exists(module_path: str) -> bool:
    parts = module_path.split(".")
    rel = os.path.join(*parts) + ".py"
    return os.path.exists(rel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Docs consistency check.")
    parser.parse_args(argv)

    content = _load_runbook()
    if content is None:
        _print("fail", "runbook_missing")
        return 1

    for token in REQUIRED_TOKENS:
        if token not in content:
            _print("fail", "missing_token")
            return 1

    if SUSPICIOUS_DSN.search(content):
        _print("fail", "suspicious_dsn")
        return 1

    for module in MODULE_REFERENCES:
        if not _module_exists(module):
            _print("fail", "missing_module")
            return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
