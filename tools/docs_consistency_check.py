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

LAUNCH_REQUIRED_TOKENS = [
    "pre_release_gate",
    "prod_rehearsal",
    "restore_dry_run",
    "secret_echo_guard",
]

MODULE_REFERENCES = [
    "tools.db_bootstrap",
    "tools.db_verify",
    "tools.ops_ci_normalize",
    "tools.prod_config_contract",
]

RUNBOOK_PATH = os.path.join("docs", "operator_runbook.md")
LAUNCH_CHECKLIST_PATH = os.path.join("docs", "launch_checklist.md")
GO_NO_GO_TEMPLATE_PATH = os.path.join("docs", "go_no_go_template.md")
V1_COMPLETE_PATH = os.path.join("docs", "V1_COMPLETE.md")
STAGED_ROLLOUT_PATH = os.path.join("docs", "staged_rollout.md")
REGRESSION_BASELINE_PATH = os.path.join("docs", "regression_baseline.md")

SUSPICIOUS_DSN = re.compile(r"postgres://[^\s:]+:[^\s@]+@")


def _print(status: str, reason: str | None = None) -> None:
    line = f"docs_check status={status}"
    if reason:
        line = f"{line} reason={reason}"
    print(line)


def _load_text(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _module_exists(module_path: str) -> bool:
    parts = module_path.split(".")
    rel = os.path.join(*parts) + ".py"
    return os.path.exists(rel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Docs consistency check.")
    parser.parse_args(argv)

    runbook = _load_text(RUNBOOK_PATH)
    if runbook is None:
        _print("fail", "runbook_missing")
        return 1

    for token in REQUIRED_TOKENS:
        if token not in runbook:
            _print("fail", "missing_token")
            return 1

    launch_checklist = _load_text(LAUNCH_CHECKLIST_PATH)
    if launch_checklist is None:
        _print("fail", "launch_checklist_missing")
        return 1

    go_no_go = _load_text(GO_NO_GO_TEMPLATE_PATH)
    if go_no_go is None:
        _print("fail", "go_no_go_template_missing")
        return 1

    v1_complete = _load_text(V1_COMPLETE_PATH)
    if v1_complete is None:
        _print("fail", "v1_complete_missing")
        return 1

    staged_rollout = _load_text(STAGED_ROLLOUT_PATH)
    if staged_rollout is None:
        _print("fail", "staged_rollout_missing")
        return 1

    regression_baseline = _load_text(REGRESSION_BASELINE_PATH)
    if regression_baseline is None:
        _print("fail", "regression_baseline_missing")
        return 1

    if "docs/launch_checklist.md" not in runbook or "docs/V1_COMPLETE.md" not in runbook:
        _print("fail", "missing_launch_link")
        return 1
    if "docs/staged_rollout.md" not in runbook:
        _print("fail", "missing_rollout_link")
        return 1
    if "docs/regression_baseline.md" not in runbook:
        _print("fail", "missing_regression_link")
        return 1

    for token in LAUNCH_REQUIRED_TOKENS:
        if token not in launch_checklist:
            _print("fail", "missing_launch_token")
            return 1

    if SUSPICIOUS_DSN.search(runbook):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(launch_checklist) or SUSPICIOUS_DSN.search(go_no_go):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(v1_complete):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(staged_rollout):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(regression_baseline):
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
