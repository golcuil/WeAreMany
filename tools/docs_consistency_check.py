from __future__ import annotations

import argparse
import os
import re

RUNBOOK_PATH = os.path.join("docs", "operator_runbook.md")
LAUNCH_CHECKLIST_PATH = os.path.join("docs", "launch_checklist.md")
GO_NO_GO_TEMPLATE_PATH = os.path.join("docs", "go_no_go_template.md")
V1_COMPLETE_PATH = os.path.join("docs", "V1_COMPLETE.md")
STAGED_ROLLOUT_PATH = os.path.join("docs", "staged_rollout.md")
REGRESSION_BASELINE_PATH = os.path.join("docs", "regression_baseline.md")
CANARY_DRILL_PATH = os.path.join("docs", "canary_drill.md")
LOGGING_POLICY_PATH = os.path.join("docs", "logging_policy.md")
GOLDEN_PATH = os.path.join("docs", "OPERATOR_GOLDEN_PATH.md")
RELEASE_READINESS_PATH = os.path.join("docs", "RELEASE_READINESS.md")

SUSPICIOUS_DSN = re.compile(r"postgres://[^\s:]+:[^\s@]+@")
RETENTION_NUMERIC = re.compile(
    r"(retention|retain|keep)[^\n]{0,40}\b\d+\s*day", re.IGNORECASE
)
RETENTION_NUMERIC_ALT = re.compile(
    r"retention[-_\s]?days?\s*[:=]\s*\d+", re.IGNORECASE
)
DOC_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

BACKLINK_OP_LINE = "Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)"
BACKLINK_RELEASE_LINE = "Back to [RELEASE_READINESS](RELEASE_READINESS.md)"


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


def _extract_doc_links(text: str) -> set[str]:
    links: set[str] = set()
    for match in DOC_LINK_RE.findall(text):
        link = match.split("#", 1)[0].strip()
        if not link:
            continue
        if link.startswith("http://") or link.startswith("https://"):
            continue
        if link.startswith("./"):
            link = link[2:]
        if link.startswith("docs/"):
            normalized = os.path.normpath(link)
        elif link.endswith(".md"):
            normalized = os.path.normpath(os.path.join("docs", link))
        else:
            continue
        if normalized.startswith("docs/"):
            links.add(normalized)
    return links


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Docs consistency check.")
    parser.parse_args(argv)

    runbook = _load_text(RUNBOOK_PATH)
    if runbook is None:
        _print("fail", "runbook_missing")
        return 1

    golden_path = _load_text(GOLDEN_PATH)
    if golden_path is None:
        _print("fail", "golden_path_missing")
        return 1

    release_readiness = _load_text(RELEASE_READINESS_PATH)
    if release_readiness is None:
        _print("fail", "release_readiness_missing")
        return 1

    required_golden_links = [
        "docs/RELEASE_READINESS.md",
        "docs/operator_rehearsal.md",
        "docs/staged_rollout.md",
        "docs/regression_baseline.md",
        "docs/logging_policy.md",
        "docs/disaster_recovery.md",
        "docs/launch_checklist.md",
    ]
    for link in required_golden_links:
        if link not in golden_path:
            _print("fail", "missing_golden_path_link")
            return 1

    required_release_links = [
        "docs/OPERATOR_GOLDEN_PATH.md",
        "docs/launch_checklist.md",
        "docs/staged_rollout.md",
        "docs/disaster_recovery.md",
        "docs/logging_policy.md",
    ]
    for link in required_release_links:
        if link not in release_readiness:
            _print("fail", "missing_release_readiness_link")
            return 1

    must_exist = {
        GOLDEN_PATH,
        RELEASE_READINESS_PATH,
        RUNBOOK_PATH,
    }
    must_exist.update(_extract_doc_links(golden_path))
    must_exist.update(_extract_doc_links(release_readiness))

    for path in sorted(must_exist):
        if not os.path.exists(path):
            _print("fail", "required_doc_missing")
            return 1

    audit_if_exists = {
        os.path.join("docs", "ops_playbook.md"),
        os.path.join("docs", "threat_model.md"),
        os.path.join("docs", "secret_rotation.md"),
        os.path.join("docs", "go_no_go_template.md"),
        os.path.join("docs", "V1_COMPLETE.md"),
    }

    audited_docs = set(must_exist)
    audited_docs.update({doc for doc in audit_if_exists if os.path.exists(doc)})
    audited_docs.discard(GOLDEN_PATH)
    audited_docs.discard(RELEASE_READINESS_PATH)

    for doc_path in sorted(audited_docs):
        doc_text = _load_text(doc_path)
        if doc_text is None:
            _print("fail", "required_doc_missing")
            return 1
        if BACKLINK_OP_LINE not in doc_text or BACKLINK_RELEASE_LINE not in doc_text:
            _print("fail", "missing_backlink")
            return 1

    if SUSPICIOUS_DSN.search(runbook):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(golden_path):
        _print("fail", "suspicious_dsn")
        return 1
    if SUSPICIOUS_DSN.search(release_readiness):
        _print("fail", "suspicious_dsn")
        return 1

    retention_sources = "\n".join(
        [
            runbook,
            golden_path,
            release_readiness,
        ]
    )
    if RETENTION_NUMERIC.search(retention_sources) or RETENTION_NUMERIC_ALT.search(
        retention_sources
    ):
        _print("fail", "retention_numeric")
        return 1

    _print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
